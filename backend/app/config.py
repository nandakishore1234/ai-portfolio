from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.keys import parse_keys

BACKEND_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = BACKEND_DIR / "app" / "knowledge"
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
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
    livekit_url: str = "ws://127.0.0.1:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secretsecretsecretsecretsecretsecret12"
    livekit_room_prefix: str = "nanda-voice"
    voice_api_base: str = "http://127.0.0.1:8000"
    voice_idle_processes: int = 2

    google_api_key: str = ""
    gemini_api_key: str = ""
    gemini_api_keys: str = ""
    gemini_api_key_1: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    gemini_api_key_5: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "gemini-embedding-001"

    cartesia_api_key: str = ""
    cartesia_api_keys: str = ""
    cartesia_api_key_1: str = ""
    cartesia_api_key_2: str = ""
    cartesia_api_key_3: str = ""
    cartesia_api_key_4: str = ""
    cartesia_api_key_5: str = ""
    cartesia_stt_model: str = "ink-2"
    cartesia_stt_language: str = "en"
    cartesia_tts_model: str = "sonic-3"
    cartesia_tts_language: str = "en"
    cartesia_tts_voice_id: str = "f786b574-daa5-4673-aa0c-cbe3e8534c02"
    cartesia_tts_voice_id_1: str = ""
    cartesia_tts_voice_id_2: str = ""
    cartesia_tts_voice_id_3: str = ""
    cartesia_tts_voice_id_4: str = ""
    cartesia_tts_voice_id_5: str = ""
    cartesia_tts_speed: float = 1.0
    admin_username: str = "admin"
    admin_password: str = ""
    admin_secret: str = ""
    seaweedfs_filer_url: str = "http://127.0.0.1:8888"
    seaweedfs_prefix: str = "/nanda-calls"
    ga_measurement_id: str = ""
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def gemini_keys(self) -> list[str]:
        return parse_keys(
            self.google_api_key,
            self.gemini_api_key,
            self.gemini_api_keys,
            self.gemini_api_key_1,
            self.gemini_api_key_2,
            self.gemini_api_key_3,
            self.gemini_api_key_4,
            self.gemini_api_key_5,
        )

    @property
    def cartesia_keys(self) -> list[str]:
        return parse_keys(
            self.cartesia_api_key,
            self.cartesia_api_keys,
            self.cartesia_api_key_1,
            self.cartesia_api_key_2,
            self.cartesia_api_key_3,
            self.cartesia_api_key_4,
            self.cartesia_api_key_5,
        )

    @property
    def cartesia_key_voices(self) -> dict[str, str]:
        default = (self.cartesia_tts_voice_id or "").strip()
        slots = (
            (self.cartesia_api_key_1, self.cartesia_tts_voice_id_1),
            (self.cartesia_api_key_2, self.cartesia_tts_voice_id_2),
            (self.cartesia_api_key_3, self.cartesia_tts_voice_id_3),
            (self.cartesia_api_key_4, self.cartesia_tts_voice_id_4),
            (self.cartesia_api_key_5, self.cartesia_tts_voice_id_5),
        )
        voices: dict[str, str] = {}
        for key, voice in slots:
            key = (key or "").strip()
            if not key:
                continue
            voices[key] = (voice or "").strip() or default
        for key in self.cartesia_keys:
            voices.setdefault(key, default)
        return voices


settings = Settings()
