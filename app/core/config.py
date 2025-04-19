from pydantic import BaseSettings

class Settings(BaseSettings):
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_EXTENSIONS = {"csv"}

    class Config:
        env_file = ".env"

settings = Settings()
