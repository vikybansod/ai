# Local DynamoDB with seeded data

docker build -t ecommerce-seed:1.0.0 agent_ai/ecommerce
kubectl apply -f agent_ai/ecommerce/k8s.yaml
kubectl wait --for=condition=complete job/ecommerce-seed --timeout=300s
kubectl logs job/ecommerce-seed

# Local ecommerce sample database

See [ecommerce/README.md](ecommerce/README.md) for DynamoDB Local with sample products, customers, and orders on your MacBook.

# To run agent in local
source .venv313/bin/activate
python server.py

//or

docker run -it --rm -p 8080:8080 -e OPENAI_API_KEY=${OPENAI_API_KEY} strands_agent:1.0.4

//or

envsubst '${OPENAI_API_KEY}' < strands/k8s.yaml | kubectl apply -f -

# To run Chainlit UI from local
export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
chainlit run ui/app.py --host 127.0.0.1 --port 8000

//or

export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"


docker build -t chainlit_ui:1.0.0 -f ui/Dockerfile ui

export AGENT_URL="http://strands-agent:8080/chat"
export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
envsubst '${AGENT_URL} ${CHAINLIT_AUTH_SECRET}' < ui/k8s.yaml | kubectl apply -f -
