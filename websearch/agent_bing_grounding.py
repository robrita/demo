# Before running the sample:
#    pip install --pre azure-ai-projects>=2.0.0b1
#    pip install azure-identity

import time

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://r0bfoundry.services.ai.azure.com/api/projects/r0bAgents"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

myAgent = "robai"
myVersion = "7"

openai_client = project_client.get_openai_client()

# Warm up auth + TLS connection pool without creating a message
try:
    openai_client.models.list()
except Exception:
    pass

# Reference the agent to get a response
start_time = time.perf_counter()
response = openai_client.responses.create(
    input=[{"role": "user", "content": "whats the weather in seattle today?"}],
    extra_body={"agent_reference": {"name": myAgent, "version": myVersion, "type": "agent_reference"}},
)
elapsed = time.perf_counter() - start_time

print(f"Response output: {response.output_text}")
print(f"Response time: {elapsed:.2f}s")
