import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    n8n_base_url: str
    n8n_api_key: str
    app_password: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        n8n_base_url=os.environ["N8N_BASE_URL"],
        n8n_api_key=os.environ["N8N_API_KEY"],
        app_password=os.environ["APP_PASSWORD"],
    )