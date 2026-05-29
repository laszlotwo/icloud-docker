from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # AI provider: "gemini" or "claude"
    AI_PROVIDER: str = "gemini"
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    SECRET_KEY: str = "dev-secret-change-in-production"
    DATABASE_URL: str = "sqlite:////data/home_ai.db"
    DATA_DIR: str = "/data"
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    LOG_LEVEL: str = "info"
    VAULT_SESSION_TIMEOUT_MINUTES: int = 30
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
