from strands import tool
from datetime import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import os
from decimal import Decimal

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

geolocator = Nominatim(user_agent="city_time_tool")
tf = TimezoneFinder()


def _json_value(value):
    """Convert DynamoDB numbers recursively to JSON-compatible values."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


@tool
def lookup_order(order_id: str) -> dict:
    """Look up an ecommerce order by ID, including items, total and status.

    Args:
        order_id: Order ID to look up, for example O001.

    Returns:
        Stored order details, or an error if the ID is empty, missing, or the
        database cannot be reached. Optional details are returned only if stored.
    """
    normalized_id = order_id.strip().upper()
    if not normalized_id:
        return {"error": "Please provide an order ID, for example O001."}

    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:8001")
    try:
        # Explicit dummy credentials keep this local testing tool independent
        # of AWS profiles and pod credentials. Construct lazily on each call.
        db = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint,
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            aws_access_key_id="local",
            aws_secret_access_key="local",
            config=Config(connect_timeout=3, read_timeout=5,
                          retries={"mode": "standard", "total_max_attempts": 2}),
        )
        response = db.Table(os.environ.get("ORDERS_TABLE", "ecommerce_orders")).get_item(
            Key={"order_id": normalized_id}, ConsistentRead=True,
        )
    except (BotoCoreError, ClientError):
        return {"error": "Unable to retrieve order details. Check the DynamoDB endpoint and orders table configuration."}

    item = response.get("Item")
    if not item:
        return {"error": f"Order {normalized_id} not found. Please verify the order ID and try again."}
    return _json_value(item)

@tool
def get_current_time(city: str) -> str:
    """Get the current time in a given city.
    Args:
        city: Name of the city to get the time for.
    """
    location = geolocator.geocode(city)

    if not location:
        return f"Could not find location for '{city}'."
    
    tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if not tz_name:
        return f"Could not determine timezone for '{city}'"

    tz = ZoneInfo(tz_name)
    return datetime.now(tz).strftime("%H:%M:%S")
