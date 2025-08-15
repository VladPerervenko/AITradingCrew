import os
import requests


from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")
model_id = "gpt-5-nano-2025-08-07" #"gpt-4.1-nano-2025-04-14"
url = "https://api.llm7.io/v1/chat/completions"

payload = {
    "model": model_id,
    "messages": [{"role": "user", "content": "Say hello"}]
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code)
print(response.json())
