import os

from dotenv import load_dotenv
from entsoe import EntsoePandasClient


def get_client() -> EntsoePandasClient:
    """Load API key from environment and return an ENTSO-E client."""
    load_dotenv()
    api_key = os.environ["ENTSOE_API_KEY"]
    return EntsoePandasClient(api_key=api_key)
