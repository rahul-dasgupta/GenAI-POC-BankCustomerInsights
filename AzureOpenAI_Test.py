import os
from openai import OpenAI

deployment = os.environ.get("OPENAI_DEPLOYMENT", "model-router")

endpoint = os.environ.get("OPENAI_ENDPOINT")
api_key = os.environ.get("OPENAI_API_KEY")

if not endpoint:
    raise ValueError("Set OPENAI_ENDPOINT to your Azure OpenAI resource URL.")

if not api_key:
    raise ValueError("Set OPENAI_API_KEY to an Azure OpenAI API key.")

base_url = endpoint.rstrip("/") + "/openai/v1/"

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

response = client.responses.create(
    model=deployment,
    input=[
        {
            "role": "system",
            "content": [{"type": "input_text", "text": "You are a helpful assistant."}],
        },
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "I am going to Paris, what should I see?"}],
        },
    ],
    max_output_tokens=4096,
)

print(response.output_text)
