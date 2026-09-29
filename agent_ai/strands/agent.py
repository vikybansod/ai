from strands import Agent
from strands.models import OpenAIModel
from tool import get_current_time

# Initialize your agent
agent = Agent(
    model=OpenAIModel(model_id="gpt-4o"),
    system_prompt="You are a helpful assistant that can do simple calculation get the location and tell the current time for that location.",
    tools=[get_current_time],
)

prompt="""
"What is the current time in New York?"
"""

# Send a message to the agent
response = agent(prompt)
# print(response)