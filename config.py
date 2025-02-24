"""Config Module. Contains the Config class."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv


class _Config:
    """Config class. Manages env vars."""

    def __init__(self) -> None:
        """Initialize config class."""
        self._parse_environment_files()

        self._words_generation_interval = int(os.getenv("WORDS_GENERATION_INTERVAL", 5))

        if self._words_generation_interval < 5:
            raise ValueError("WORDS_GENERATION_INTERVAL must be at least 5")

        self._apigw_custom_header_name = "apigw-cloudfront-token"

    @staticmethod
    def _parse_environment_files() -> None:
        """Load the .env file."""

        if not os.path.isfile(".env"):
            raise RuntimeError(".env is missing")
        load_dotenv(".env", verbose=True)


@dataclass
class BaseConfig(_Config):
    """BaseConfig that is available to all modules."""

    def __init__(
        self,
    ) -> None:
        """Construct a new BaseConfig."""
        super().__init__()

    @property
    def apigw_custom_header_name(self):
        """Custom header name for API Gateway."""
        return self._apigw_custom_header_name

    @property
    def words_generation_interval(self):
        """Read-only property for words_generation_interval."""
        return self._words_generation_interval

    @property
    def apigw_custom_header_parameter_name(self) -> str:
        """Get the SSM secure parameter name."""

        return self._apigw_custom_header_name
