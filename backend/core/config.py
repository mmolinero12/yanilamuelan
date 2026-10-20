from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator
from shared.config import ENV_FILE

class Settings(BaseSettings):

    app_name: str = "NuevaMente"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = Field(default=False, validation_alias=AliasChoices("APP_DEBUG", "DEBUG"))

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    llm_provider: str = "gemini"

    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    vector_store: str = "chroma"
    top_k: int = Field(default=5, ge=1, le=50)
    vectorstore_path: str = "./data/vectorstore"

    oci_config_file: str = "~/.oci/config"
    oci_profile: str = "DEFAULT"
    oci_namespace: str | None = None
    oci_bucket_name: str | None = None
    oci_region: str | None = None

    documents_path: str = "./data/documents"
    generated_path: str = "./data/generated"
    max_upload_mb: int = Field(default=10, ge=1, le=50)

    log_level: str = "INFO"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        # Algunos entornos Windows definen DEBUG=release globalmente.
        return False if isinstance(value, str) and value.lower() == "release" else value

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    
settings = Settings()
