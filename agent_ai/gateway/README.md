# Envoy AI Gateway for the Strands agent

Flow: Chainlit → Strands → Envoy AI Gateway → OpenAI. The agent uses a placeholder SDK credential. `BackendSecurityPolicy` injects the real credential from the `ai-gateway-openai` Secret; the agent Deployment has no OpenAI Secret reference.

These manifests target Docker Desktop Kubernetes with application resources in `default`. Helm versions are pinned to Envoy Gateway v1.5.4 and Envoy AI Gateway v0.5.0. Integration values are copied from the official v0.5.0 release. This is a local testing configuration with an internal ClusterIP HTTP listener.

## Install with Helm

Install Helm if needed (`brew install helm`). Run these commands from the repository root:

```sh
helm upgrade --install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.5.4 -n envoy-gateway-system --create-namespace \
  -f agent_ai/gateway/envoy-gateway-values.yaml --wait --timeout 5m
helm upgrade --install aieg-crd oci://docker.io/envoyproxy/ai-gateway-crds-helm \
  --version v0.5.0 -n envoy-ai-gateway-system --create-namespace
helm upgrade --install aieg oci://docker.io/envoyproxy/ai-gateway-helm \
  --version v0.5.0 -n envoy-ai-gateway-system --create-namespace --wait --timeout 5m
```

Create the gateway's credential Secret using an exported `OPENAI_API_KEY`. This pipes the value directly to kubectl without saving it to a file or passing it as a process argument:

```sh
python3 - <<'PY' | kubectl apply -f -
import json, os
print(json.dumps({
    "apiVersion": "v1", "kind": "Secret", "type": "Opaque",
    "metadata": {"name": "ai-gateway-openai", "namespace": "default"},
    "stringData": {"apiKey": os.environ["OPENAI_API_KEY"]},
}))
PY
kubectl apply -f agent_ai/gateway/k8s.yaml
kubectl wait --for=condition=Programmed gateway/ecommerce-ai --timeout=180s
```

Only `gpt-4o` is routed. To change the model, update the model ID in `strands/agent.py` and the model match in `gateway/k8s.yaml` together.

## Deploy the agent

```sh
docker build -t strands_agent:1.0.6 agent_ai/strands
kubectl apply -f agent_ai/strands/k8s.yaml
kubectl rollout status deployment/strands-agent --timeout=120s
```

Load the image into the cluster if your provisioner uses a separate image store. After the new agent is healthy, remove the old direct-access Secret if it exists:

```sh
kubectl delete secret strands-agent-openai --ignore-not-found
```

The agent URL is `http://ai-gateway.envoy-gateway-system.svc.cluster.local/v1`. The stable `ai-gateway` Service selects Envoy's generated data-plane pods. The model client defaults to `http://localhost:8081/v1` for local Python execution, with no direct OpenAI fallback.

## Local access and verification

In a separate terminal:

```sh
kubectl port-forward -n envoy-gateway-system service/ai-gateway 8081:80
```

Send a request without an OpenAI credential:

```sh
curl --fail-with-body http://localhost:8081/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"Say hello briefly."}],"max_tokens":20}'
```

For local Python, set `AI_GATEWAY_URL=http://localhost:8081/v1`. For a local Docker agent, use `http://host.docker.internal:8081/v1`. Test the deployed agent through Chainlit with `Get order details for O001`; this exercises streaming model calls, the DynamoDB tool, and the model's final response.

Troubleshooting:

```sh
kubectl get gateway,aigatewayroute,aiservicebackend,backendsecuritypolicy -n default
kubectl get pods,services -n envoy-gateway-system
kubectl logs -n envoy-ai-gateway-system deployment/ai-gateway-controller --tail=50
```

References: [official pinned installation guide](https://github.com/envoyproxy/ai-gateway/blob/v0.5.0/site/docs/getting-started/installation.md), [OpenAI configuration](https://github.com/envoyproxy/ai-gateway/blob/v0.5.0/examples/basic/openai.yaml).
