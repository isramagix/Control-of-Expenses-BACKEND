
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    class Config:
        env_file = ".env"
        encoding = "utf-8"

try:
    s = Settings()
    print("OK:", s.model_dump())
except Exception as e:
    print("ERROR leyendo .env:", repr(e))
