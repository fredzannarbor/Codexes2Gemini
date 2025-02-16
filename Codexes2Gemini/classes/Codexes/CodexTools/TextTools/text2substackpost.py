"""
GrokStack: a substack helper powered by Grok
- Compose a daily letter to yourself
- Compose daily newsletters on themes of your choice
- Create paywallable special features
- Streamlit UI
- use openai api library
"""
import os
from openai import OpenAI

XAI_API_KEY = os.getenv("XAI_API_KEY")
client = OpenAI(
    api_key="xai-IIlClv1eVXjg8lFMSyiI6hgzL9tiywcfnqGb7RUdopZ7Esq8ZH8LGT8FnjQjWcRQJ07bP7SP3Tpk8giC",
    base_url="https://api.x.ai/v1",
)

completion = client.chat.completions.create(
    model="grok-beta",
    messages=[
        {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."},
        {"role": "user", "content": question},
    ],
)


def compose_item(prompt):


if __name__ == "__main__":
    question = "Please list the five recently published books that have received the most interest in the last 24 hours."

    compose_item(question)
