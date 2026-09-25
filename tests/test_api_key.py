import os
from dotenv import load_dotenv
from google import genai

def test_api_key_loads():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key is not None, "API key should be loaded from .env"

def test_client_initialization():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    assert client is not None

def test_reply():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")  
    assert api_key is not None, "API key must be set in .env"

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input="Hello, how are you?"
    )

    print("Response from API:", interaction.output_text)
    assert interaction.output_text is not None