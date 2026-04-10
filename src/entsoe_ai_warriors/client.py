import os

from dotenv import load_dotenv
from entsoe import EntsoePandasClient


def get_client() -> EntsoePandasClient:
    load_dotenv()
    api_key = os.getenv("ENTSOE_API_KEY")
    if not api_key:
        raise RuntimeError("ENTSOE_API_KEY is not set in environment or .env file")
    return EntsoePandasClient(api_key=api_key)
