"""Provision local Langfuse project/login and collector credentials without printing them."""
import base64
import json
import secrets
import subprocess


def kubectl(*args, **kwargs):
    return subprocess.run(["kubectl", *args], check=True, **kwargs)


for namespace in ("langfuse", "observability"):
    manifest = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": namespace}}
    kubectl("apply", "-f", "-", input=json.dumps(manifest), text=True)

existing = subprocess.run(
    ["kubectl", "get", "secret", "langfuse-bootstrap", "-n", "langfuse", "-o", "json", "--ignore-not-found"],
    check=True, capture_output=True, text=True,
).stdout
if existing.strip():
    data = {k: base64.b64decode(v).decode() for k, v in json.loads(existing)["data"].items()}
else:
    data = {
        "LANGFUSE_INIT_ORG_ID": "local-ecommerce",
        "LANGFUSE_INIT_ORG_NAME": "Local Ecommerce",
        "LANGFUSE_INIT_PROJECT_ID": "strands-agent",
        "LANGFUSE_INIT_PROJECT_NAME": "Strands Agent",
        "LANGFUSE_INIT_PROJECT_PUBLIC_KEY": "pk-lf-" + secrets.token_hex(16),
        "LANGFUSE_INIT_PROJECT_SECRET_KEY": "sk-lf-" + secrets.token_hex(24),
        "LANGFUSE_INIT_USER_EMAIL": "admin@example.com",
        "LANGFUSE_INIT_USER_NAME": "Local Admin",
        "LANGFUSE_INIT_USER_PASSWORD": secrets.token_urlsafe(24),
    }
    kubectl("apply", "-f", "-", input=json.dumps({
        "apiVersion": "v1", "kind": "Secret", "type": "Opaque",
        "metadata": {"name": "langfuse-bootstrap", "namespace": "langfuse"}, "stringData": data,
    }), text=True)
auth = "Basic " + base64.b64encode((data["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"] + ":" + data["LANGFUSE_INIT_PROJECT_SECRET_KEY"]).encode()).decode()
kubectl("apply", "-f", "-", input=json.dumps({
    "apiVersion": "v1", "kind": "Secret", "type": "Opaque",
    "metadata": {"name": "langfuse-exporter", "namespace": "observability"},
    "stringData": {"authorization": auth},
}), text=True)
