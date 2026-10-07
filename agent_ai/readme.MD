# Local DynamoDB with seeded data

docker build -t ecommerce-seed:1.0.0 agent_ai/ecommerce
kubectl apply -f agent_ai/ecommerce/k8s.yaml
kubectl wait --for=condition=complete job/ecommerce-seed --timeout=300s
kubectl logs job/ecommerce-seed

# Local ecommerce sample database

See [ecommerce/README.md](ecommerce/README.md) for DynamoDB Local with sample products, customers, and orders on your MacBook.

# Envoy AI Gateway

See [gateway/README.md](gateway/README.md) for Helm installation, gateway-owned OpenAI credentials, and local port-forwarding. The agent uses `AI_GATEWAY_URL` and no longer needs `OPENAI_API_KEY`.

# To run agent in local
The agent supports order lookup (try `Get order details for O001`). For local Python execution, DynamoDB defaults to `http://localhost:8001`; use the ecommerce port-forward when it runs in Kubernetes. The defaults are `ORDERS_TABLE=ecommerce_orders` and `AWS_REGION=us-east-1`.

To deploy the updated agent to Docker Desktop Kubernetes, run from `agent_ai`:

```sh
docker build -t strands_agent:1.0.6 strands
kubectl apply -f strands/k8s.yaml
kubectl rollout status deployment/strands-agent
```

Deploy it in the same namespace as the ecommerce database, or update `DYNAMODB_ENDPOINT_URL` in `strands/k8s.yaml` to the database Service's namespace-qualified address. Load the new image into the cluster if its image store is separate from Docker's. The tool uses dummy DynamoDB credentials for this local test setup.

source .venv313/bin/activate
python server.py

//or

docker run -it --rm -p 8080:8080 -e AI_GATEWAY_URL=http://host.docker.internal:8081/v1 strands_agent:1.0.6

//or

kubectl apply -f strands/k8s.yaml

# To run Chainlit UI from local
export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
chainlit run ui/app.py --host 127.0.0.1 --port 8000

//or

export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"


docker build -t chainlit_ui:1.0.0 -f ui/Dockerfile ui

export AGENT_URL="http://strands-agent:8080/chat"
export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
envsubst '${AGENT_URL} ${CHAINLIT_AUTH_SECRET}' < ui/k8s.yaml | kubectl apply -f -
