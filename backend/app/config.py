from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = BACKEND_DIR / "app" / "knowledge"
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "qwen2"
    ollama_embed_model: str = "nomic-embed-text"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "nanda_portfolio"
    qdrant_path: str = ""
    rag_top_k: int = 4
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    contact_to_email: str = "knandakishore6@gmail.com"
    resend_api_key: str = ""
    resend_from_email: str = "Portfolio <onboarding@resend.dev>"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
