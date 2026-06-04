from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracoes(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    GEMINI_API_KEY: str
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


configuracoes = Configuracoes()
