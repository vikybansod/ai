from strands import Agent
from strands.models import OpenAIModel

# Initialize your agent
agent = Agent(
    model=OpenAIModel(model_id="gpt-4o"),
    system_prompt="You are a helpful assistant that provides concise responses."
)

# Send a message to the agent
response=agent("tell me a joke")