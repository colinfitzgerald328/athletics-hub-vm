import os 
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT")

import vertexai
from vertexai.preview.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models

vertexai.init(project=GCLOUD_PROJECT)

import requests

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIAIAdaptor:
    """OpenAI adaptor"""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_response(self, prompt: str, json_mode: bool = False) -> str:
        """
        Generates a response from OpenAI given a prompt
        """
        params = {
            "model": "gpt-4-0125-preview",
            "messages": [{"role": "system", "content": prompt}],
        }

        if json_mode:
            params["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content


class GoogleGenAIAdaptor:
    """Google GenAI adaptor"""

    def generate(self, prompt: str) -> str:
        model = GenerativeModel("gemini-pro")
        responses = model.generate_content(
            prompt,
            generation_config={"temperature": 0.9, "top_p": 1},
            safety_settings={
                generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            stream=True,
        )
        retries = 0
        while retries < 3:
            try:
                return "".join([response.text for response in responses])
            except Exception as e:
                logger.info(f"Model failed on api call # {retries}, error was" + str(e))
                retries += 1
        return None


class DeepInfraAIAdaptor:
    """DeepInfra AI adaptor"""

    def generate(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        }

        json_data = {
            "model": "deepinfra/airoboros-70b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "top_p": 0.2,
        }

        response = requests.post(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            headers=headers,
            json=json_data,
        )
        result = response.json()["choices"][0]["message"]["content"]
        return result
