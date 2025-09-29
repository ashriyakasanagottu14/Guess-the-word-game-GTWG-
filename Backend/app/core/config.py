from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = Field(default="word-guess-backend")
    APP_ENV: str = Field(default="dev")
    APP_DEBUG: bool = Field(default=True)
    API_PREFIX: str = Field(default="/api/v1")

    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB: str = Field(default="word_guess")

    JWT_SECRET: str = Field(default="wTCWuWkiXwnq74ESrsTtFI3zEPFQQA7-5YNPN6Ed0KvTlsQI86dpBCHqH3jW1isCqCv6JASFU_U9PEcbtI8V6iqGqhaL83eSv89qP1Y99Iqw730zgKu3LjC3d1H8lmBc-AZll_UaODg2uVLjYIbbtYWV72DQRXn1Yl236xGTbASOsP4FXDlXuWDtSt1M32ua72JBbeffCXVQpMOH7P-0sBZMEy97Zv9NugHrx5VTnTz2WUd4oGvyfoNOq8lix9P73Y4BUX0RrE2Uvp6Ix0pPmCJhdz4Y2NR3mnc6I5W5GTg9U49iKwrLUbeD28hOfRUrv0bOhOCx_TdQftBnfg0hmA")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRES_MINUTES: int = Field(default=60 * 24)

    ADMIN_DEFAULT_USERNAME: str = Field(default="AdminUser")
    ADMIN_DEFAULT_PASSWORD: str = Field(default="Adm1n$*")

    # Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="")
    SMTP_FROM_NAME: str = Field(default="Guess The Word Game")


    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
