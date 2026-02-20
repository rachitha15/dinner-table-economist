import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    mospi_mcp_url: str = os.getenv("MOSPI_MCP_URL", "https://mcp.mospi.gov.in")
    allow_origins: list[str] = field(
        default_factory=lambda: os.getenv("ALLOW_ORIGINS", "*").split(",")
    )
    openai_ssl_verify: bool = os.getenv("OPENAI_SSL_VERIFY", "true").lower() != "false"
    app_api_key: str | None = os.getenv("APP_API_KEY")


settings = Settings()
