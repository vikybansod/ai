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