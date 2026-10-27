import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


def get_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=os.environ["DIAL_ENDPOINT"],
        api_key=os.environ["DIAL_API_KEY"],
        api_version=os.environ["DIAL_API_VERSION"],
        azure_deployment=os.environ["DIAL_DEPLOYMENT"],
    )