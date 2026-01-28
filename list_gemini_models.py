from google import genai
import os

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

for model in client.models.list():
    print(model.name)