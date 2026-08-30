from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6",
    input="Hello from FPL Stato! Give me a one-sentence welcome."
)

print(response.output_text)
