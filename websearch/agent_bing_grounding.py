# Before running the sample:
#    pip install --pre azure-ai-projects>=2.0.0b1
#    pip install azure-identity

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://r0bfoundry.services.ai.azure.com/api/projects/r0bAgents"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

myAgent = "robai"
myVersion = "6"

openai_client = project_client.get_openai_client()

# Reference the agent to get a response
response = openai_client.responses.create(
    input=[{"role": "user", "content": "whats the weather today in Manila?"}],
    extra_body={"agent_reference": {"name": myAgent, "version": myVersion, "type": "agent_reference"}},
)

print(f"Response output: {response.output_text}")
