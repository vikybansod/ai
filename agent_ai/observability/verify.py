"""Query recent Langfuse v4 observations without displaying project credentials."""
import base64
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import subprocess
from urllib.parse import urlencode

secret = json.loads(subprocess.check_output([
    "kubectl", "get", "secret", "langfuse-bootstrap", "-n", "langfuse", "-o", "json",
]))["data"]
auth = "Basic " + base64.b64encode(
    base64.b64decode(secret["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"]) + b":" +
    base64.b64decode(secret["LANGFUSE_INIT_PROJECT_SECRET_KEY"])
).decode()
now = datetime.now(timezone.utc)
query = urlencode({
    "fromStartTime": (now - timedelta(minutes=30)).isoformat(),
    "toStartTime": now.isoformat(),
    "limit": 100,
})
code = "\n".join([
    "import json, urllib.request",
    "request = urllib.request.Request(" + repr(
        "http://langfuse-web.langfuse.svc.cluster.local:3000/api/public/v2/observations?" + query
    ) + ", headers={'Authorization': " + repr(auth) + "})",
    "print(json.dumps(json.load(urllib.request.urlopen(request, timeout=30))))",
])
result = subprocess.run([
    "kubectl", "exec", "-i", "deployment/strands-agent", "--", "python", "-",
], input=code, text=True, check=True, capture_output=True)
observations = json.loads(result.stdout)["data"]
print(f"Recent observations: {len(observations)}")
for (name, kind), count in Counter(
    (observation.get("name"), observation.get("type")) for observation in observations
).items():
    print(f"{name}: {kind} ({count})")
if not any("lookup_order" in observation.get("name", "") for observation in observations):
    raise SystemExit("No recent order tool span yet. Run an order lookup, wait for ingestion, and retry.")
