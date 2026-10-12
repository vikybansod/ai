# MCP tool server

The agent discovers `lookup_order` and `get_current_time` from this server using Streamable HTTP at `/mcp`. Their implementations live in `tools.py`; the agent no longer imports or executes them locally. The server adapts the reference FastMCP application to the existing local DynamoDB order schema.

Flow: Chainlit → Strands → MCP server → DynamoDB (order tool). Model calls remain Strands → Envoy AI Gateway → OpenAI. Strands continues exporting agent, model, and tool spans through the existing OpenTelemetry collector to Langfuse.

## Kubernetes deployment

From the repository root, deploy the MCP server before updating the agent:

```sh
docker build -t ecommerce-mcp:1.0.0 agent_ai/mcp_server
kubectl apply -f agent_ai/mcp_server/k8s.yaml
kubectl rollout status deployment/mcp-server --timeout=180s
docker build -t strands_agent:1.0.9 agent_ai/strands
kubectl apply -f agent_ai/strands/k8s.yaml
kubectl rollout status deployment/strands-agent --timeout=180s
```

Use the same namespace as the agent and DynamoDB. For a different namespace, update Service addresses and the MCP server's `MCP_ALLOWED_HOSTS` allowlist. Load images into your cluster's image store if your local provisioner requires it.

The agent receives `MCP_SERVER_URL=http://mcp-server:8080/mcp`. DynamoDB settings now belong to the MCP Deployment. The tools use dummy database credentials. This local testing service is internal ClusterIP with no client authentication; DNS rebinding protection is enabled for the listed local and cluster hostnames.

The server is stateless and uses JSON responses. HTTP probes call `/healthz`; that checks server availability, while the tool verification below also checks DynamoDB access. Strands manages tool discovery and the MCP connection; the agent HTTP server closes it at shutdown.

## Verify

Ask Chainlit `Get order details for O001`. A `lookup_order` tool execution should appear in the streamed response and Langfuse. To test the MCP protocol directly from the running agent pod without calling the model:

```sh
kubectl exec -i deployment/strands-agent -- python - <<'PY'
import os, json
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

with MCPClient(lambda: streamablehttp_client(os.environ['MCP_SERVER_URL'])) as client:
    tools = client.list_tools_sync()
    print('Discovered:', [tool.tool_name for tool in tools])
    result = client.call_tool_sync('verify-order', 'lookup_order', {'order_id': ' o001 '})
    assert result['status'] == 'success', result
    assert 'O001' in json.dumps(result), result
    print('MCP order lookup passed.')
PY
```

## Local Python

Run the MCP server in its own virtual environment, with DynamoDB accessible at localhost:8001:

```sh
python3 -m venv /tmp/ecommerce-mcp-venv
/tmp/ecommerce-mcp-venv/bin/pip install -r agent_ai/mcp_server/requirements.txt
PORT=8082 /tmp/ecommerce-mcp-venv/bin/python agent_ai/mcp_server/server.py
```

Alternatively, port-forward the deployed server:

```sh
kubectl port-forward service/mcp-server 8082:8080
```

The local agent defaults to `MCP_SERVER_URL=http://localhost:8082/mcp`. Keep your gateway port-forward running on 8081 as before. The city-time tool still needs internet access to geocode city names.

References: [Strands MCP integration](https://strandsagents.com/docs/user-guide/sdk/tools/mcp-tools/), [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
