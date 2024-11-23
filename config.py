"""Config Module. Contains the Config class."""

import os
from dotenv import load_dotenv


class _Config:
    """Config class. Manages env vars."""

    def __init__(self) -> None:
        """Initialize config class."""
        self._parse_environment_files()

    @staticmethod
    def _parse_environment_files() -> None:
        """Load the .env file."""

        if not os.path.isfile(".env"):
            raise RuntimeError(".env is missing")
        load_dotenv(".env", verbose=True)
