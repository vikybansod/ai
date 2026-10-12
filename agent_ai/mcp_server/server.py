"""Streamable HTTP MCP server for local ecommerce and city-time tools."""
import os 

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
import uvicorn

from tools import get_current_time, lookup_order

mcp = FastMCP(
    "Ecommerce Tools",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=os.environ.get(
            "MCP_ALLOWED_HOSTS",
            "localhost:*,127.0.0.1:*,mcp-server:*,mcp-server.default.svc.cluster.local:*",
        ).split(","),
    ),
)
mcp.tool()(lookup_order)
mcp.tool()(get_current_time)

@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request):
    return JSONResponse({"ok": True})

app = mcp.streamable_http_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))