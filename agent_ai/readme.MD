# To run agent in local
source .venv313/bin/activate
python server.py

# To run Chainlit UI from local
export CHAINLIT_AUTH_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
chainlit run ui/app.py --host 127.0.0.1 --port 8000