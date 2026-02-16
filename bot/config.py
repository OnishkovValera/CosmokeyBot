from dotenv import load_dotenv
from pydantic.v1 import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    POSTGRES_DRIVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    BOT_TOKEN: str
    ADMIN_ACCOUNT_ID: int
    ADMIN_ACCOUNT_USERNAME : str
    ADMIN_GROUP_ID: int
    TELEGRAM_CHANEL_LINK: str

    class Config:
        env_file = ".env"

settings = Settings()