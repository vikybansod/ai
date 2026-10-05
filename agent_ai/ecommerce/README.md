# Local ecommerce sample data

This is an independent testing fixture inspired by the AWS workshop, not a verified copy of its schema. It provides DynamoDB Local and fictional data: 10 products, 5 customers, and 8 orders. No AWS account or real credentials are needed. Start Docker Desktop first.

From the repository root:

```sh
cd agent_ai/ecommerce
docker compose up -d dynamodb
docker compose run --rm seed
```

The seed command waits for the database, creates the tables, and inserts the JSON data. Running it again restores the sample records by ID; other records remain. Data persists in a Docker volume when containers stop.

Tables and string partition keys:

| Table | Key |
| --- | --- |
| ecommerce_products | product_id |
| ecommerce_customers | customer_id |
| ecommerce_orders | order_id |

Products include prices, categories, and stock (including an out-of-stock item). Orders include customer references, line items, totals, and different fulfillment statuses. Prices are illustrative USD amounts. Edit `sample-data.json` and rerun the seed command to change the fixtures.

## Run in Kubernetes on your Mac

For Docker Desktop Kubernetes, build the seed image locally and apply the manifest from the repository root:

```sh
docker build -t ecommerce-seed:1.0.0 agent_ai/ecommerce
kubectl apply -f agent_ai/ecommerce/k8s.yaml
kubectl rollout status deployment/ecommerce-dynamodb --timeout=180s
kubectl wait --for=condition=complete job/ecommerce-seed --timeout=300s
kubectl logs job/ecommerce-seed
```

Check `kubectl config current-context` before applying. These commands use the current namespace; keep the database and seed Job together. Your cluster needs a default StorageClass to provision the 1Gi persistent volume. The deployment runs one replica with a Recreate strategy so only one process writes to the database file. It runs as root to write to the mounted volume in this local testing setup.

If your Docker Desktop Kubernetes provisioner does not share Docker's image store, load the image into its node image store or push it to a reachable registry and update the Job's image. For kind, run `kind load docker-image ecommerce-seed:1.0.0 --name YOUR_CLUSTER`; for minikube, run `minikube image load ecommerce-seed:1.0.0` before applying.

From an application pod in the same namespace, connect to `http://dynamodb:8000` with dummy credentials as in the Python example below. From a different namespace, use `http://dynamodb.DATABASE_NAMESPACE.svc.cluster.local:8000`. The seed script uses the same-namespace Service name.

To query from your Mac, keep this command running in another terminal, then use the Python example:

```sh
kubectl port-forward service/dynamodb 8001:8000 --address 127.0.0.1
```

Stop the Compose database first if it already occupies port 8001. Kubernetes uses its own persistent volume; existing Compose data is not migrated.

After editing sample data or the seed script, rebuild the image, remove the completed Job, and apply again:

```sh
docker build -t ecommerce-seed:1.0.0 agent_ai/ecommerce
kubectl delete job ecommerce-seed
kubectl apply -f agent_ai/ecommerce/k8s.yaml
kubectl wait --for=condition=complete job/ecommerce-seed --timeout=300s
kubectl logs job/ecommerce-seed
```

For kind/minikube, reload the rebuilt image before recreating the Job. For registry deployments, use a new image tag on each rebuild. Applying an unchanged completed Job does not rerun it. To stop the database while retaining data, use `kubectl scale deployment/ecommerce-dynamodb --replicas=0`. Deleting the manifest also deletes its PVC and may delete the stored data.

## Query from Python on your Mac

Install `boto3` in your application's virtual environment (`python -m pip install -r agent_ai/ecommerce/requirements.txt` from the repository root), then use:

```python
import boto3

db = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8001",
    region_name="us-east-1",
    aws_access_key_id="local",
    aws_secret_access_key="local",
)
print(db.Table("ecommerce_products").scan()["Items"])
print(db.Table("ecommerce_orders").get_item(Key={"order_id": "O001"})["Item"])
```

Port 8001 avoids the existing Chainlit UI on port 8000. From another container in this Compose project, use `http://dynamodb:8000`. An agent running in Kubernetes needs a reachable database endpoint; its `localhost` refers to its own pod. This setup provides the database only; the existing time assistant has no ecommerce tools yet.

## Stop or reset

```sh
docker compose down
```

To delete all local ecommerce database contents and start fresh:

```sh
docker compose down -v
docker compose up -d dynamodb
docker compose run --rm seed
```

AWS documentation: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html
