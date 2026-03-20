from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    JWT_SECRET: str = ""
    JWT_PUBLIC_KEY: str = ""

    # CORS: comma-separated allowed origins
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://emojilos.github.io"

    # Rate limiting
    AUTH_RATE_LIMIT: str = "5/minute"
    API_RATE_LIMIT: str = "100/minute"
    DIAGNOSTIC_SUBMIT_RATE_LIMIT: str = "1/minute"
    STUDY_PLAN_GENERATE_RATE_LIMIT: str = "5/minute"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()  # type: ignore[call-arg]
