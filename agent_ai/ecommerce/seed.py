"""Create and seed local ecommerce tables; never uses AWS credentials."""
import json
import os
import time
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError


def main():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:8001")
    if urlparse(endpoint).hostname not in {"localhost", "127.0.0.1", "dynamodb"}:
        raise ValueError("Seed script only accepts local DynamoDB endpoints")
    db = boto3.resource(
        "dynamodb", endpoint_url=endpoint, region_name="us-east-1",
        aws_access_key_id="local", aws_secret_access_key="local",
    )
    for attempt in range(60):
        try:
            db.meta.client.list_tables()
            break
        except EndpointConnectionError:
            if attempt == 59:
                raise
            time.sleep(1)
    data = json.loads(Path(__file__).with_name("sample-data.json").read_text(), parse_float=Decimal)
    keys = {"products": "product_id", "customers": "customer_id", "orders": "order_id"}
    for name, key in keys.items():
        table = db.Table(f"ecommerce_{name}")
        try:
            table.load()
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            table = db.create_table(
                TableName=table.name,
                KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
        table.wait_until_exists()
        with table.batch_writer() as writer:
            for item in data[name]:
                writer.put_item(Item=item)
        print(f"Seeded {table.name}: {len(data[name])} records", flush=True)


if __name__ == "__main__":
    main()
