import os

from dotenv import load_dotenv


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        load_dotenv()
        required_vars = [
            "NEXT_ENDPOINT",
            "NEXT_API_KEY",
            "REDIS_HOST",
            "REDIS_PORT",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DATABASE_NAME",
            "PYTHON_TO_NEXT_QUEUE",
            "NEXT_TO_PYTHON_QUEUE",
            "EMBEDDER_SERVICE_ENDPOINT",
        ]
        optional_vars = [
            "OPENAI_API_KEY",
        ]

        for var in required_vars:
            value = os.getenv(var)
            if value is None:
                raise ValueError(f"Missing required environment variable: {var}")
            self._config[var] = value

        for var in optional_vars:
            value = os.getenv(var)
            if value is not None:
                self._config[var] = value

    def get(self, key):
        return self._config.get(key, None)


appconfig = Config()