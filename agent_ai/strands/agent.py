import os
import sys

from strands import Agent
from strands.models import OpenAIModel
from tool import get_current_time, lookup_order

# Initialize your agent
agent = Agent(
    model=OpenAIModel(
        model_id="gpt-4o",
        client_args={
            "base_url": os.environ.get("AI_GATEWAY_URL", "http://localhost:8081/v1"),
            # The SDK requires a credential; the gateway replaces this placeholder
            # with its own upstream OpenAI key. Never read OPENAI_API_KEY here.
            "api_key": "gateway-placeholder",
        },
    ),
    system_prompt=(
        "You are a helpful assistant that can do simple calculations, tell the current "
        "time for a city, and look up ecommerce orders. Use lookup_order for order "
        "details. Ask for an order ID if it is missing. Report only the details "
        "returned by the tool; do not invent shipping or tracking information."
    ),
    tools=[get_current_time, lookup_order],
)

# prompt="""
# "What is the current time in New York?"
# """

# Send a message to the agent
# response = agent(prompt)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "What is the order detail of O002"

    response = agent(prompt)
