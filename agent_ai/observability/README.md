# Local Langfuse and OpenTelemetry

Trace flow: Strands agent → OpenTelemetry Collector → Langfuse. Model traffic continues through Envoy AI Gateway. Native Strands spans record agent, model and tool execution; FastAPI and HTTPX instrumentation adds HTTP spans. This configuration exports traces only.

Langfuse has PostgreSQL, ClickHouse, a single Keeper, Valkey, and SeaweedFS with persistent volumes. The configuration is sized for local testing. API keys and the generated login password are Kubernetes Secrets, not repository files. `bootstrap.py` preserves existing credentials on reruns.

## Install from the repository root

```sh
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.20.2 -n cert-manager --create-namespace --set crds.enabled=true --wait
helm upgrade --install clickhouse-operator oci://ghcr.io/clickhouse/clickhouse-operator-helm \
  --version 0.0.8 -n clickhouse-operator --create-namespace --wait
python3 agent_ai/observability/bootstrap.py
helm upgrade --install langfuse langfuse/langfuse --version 2.1.4 \
  -n langfuse -f agent_ai/observability/langfuse-values.yaml --wait --timeout 10m
helm upgrade --install otel-collector open-telemetry/opentelemetry-collector --version 0.175.1 \
  -n observability -f agent_ai/observability/collector-values.yaml --wait --timeout 5m
docker build -t strands_agent:1.0.8 agent_ai/strands
kubectl apply -f agent_ai/strands/k8s.yaml
kubectl rollout status deployment/strands-agent --timeout=180s
```

The collector holds the Langfuse project credential and adds Basic authentication when forwarding OTLP traces. The agent requires neither a Langfuse secret nor an OpenAI key. Langfuse SDK startup authentication was replaced with collector-based export to avoid a duplicate export path.

## Open Langfuse

Keep this running in a terminal and visit http://localhost:3000:

```sh
kubectl port-forward -n langfuse service/langfuse-web 3000:3000
```

Login email: `admin@example.com`. Retrieve the generated password locally:

```sh
kubectl get secret langfuse-bootstrap -n langfuse \
  -o jsonpath='{.data.LANGFUSE_INIT_USER_PASSWORD}' | base64 --decode
```

Open the **Strands Agent** project. Ask Chainlit `Get order details for O001`, then allow a few seconds for export and ingestion before opening Traces.

Verify recent tool observations from the terminal with `python3 agent_ai/observability/verify.py`. This uses Langfuse v4's Observations API v2. The collector sends the v4 ingestion header for real-time visibility.

## Local Python execution

Port-forward the collector in another terminal:

```sh
kubectl port-forward -n observability service/otel-collector 4318:4318
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=strands-agent
```

Keep the existing gateway and DynamoDB port-forwards running, then start the agent with its virtual environment. Without `OTEL_EXPORTER_OTLP_ENDPOINT`, application instrumentation stays disabled.

## Troubleshooting

```sh
kubectl get pods,pvc -n langfuse
kubectl logs -n observability deployment/otel-collector --tail=50
kubectl logs -n langfuse deployment/langfuse-web --tail=50
kubectl logs -n langfuse deployment/langfuse-worker --tail=50
```

Traces contain prompts, model responses and tool data. Storage persists across pod restarts. Do not delete the namespaces or PVCs if you want to retain your local project and trace history.

References: [Langfuse Helm deployment](https://langfuse.com/self-hosting/deployment/kubernetes-helm), [OTLP ingestion](https://langfuse.com/integrations/native/opentelemetry), [Strands tracing](https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/traces/).
