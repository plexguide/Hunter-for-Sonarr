# src/config/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = Field('', env='API_KEY')
    api_url: str = Field('http://localhost:8989', env='API_URL')
    api_timeout: int = Field(60, env='API_TIMEOUT')
    monitored_only: bool = Field(True, env='MONITORED_ONLY')
    hunt_missing_shows: int = Field(1, env='HUNT_MISSING_SHOWS')
    hunt_upgrade_episodes: int = Field(0, env='HUNT_UPGRADE_EPISODES')
    sleep_seconds: int = Field(1800, env='SLEEP_SECONDS')
    state_reset_hours: int = Field(168, env='STATE_RESET_HOURS')
    random_missing: bool = Field(True, env='RANDOM_MISSING')
    random_upgrades: bool = Field(True, env='RANDOM_UPGRADES')
    skip_future_episodes: bool = Field(True, env='SKIP_FUTURE_EPISODES')
    skip_series_refresh: bool = Field(True, env='SKIP_SERIES_REFRESH')
    command_wait_seconds: int = Field(1, env='COMMAND_WAIT_SECONDS')
    command_wait_attempts: int = Field(600, env='COMMAND_WAIT_ATTEMPTS')
    minimum_download_queue_size: int = Field(-1, env='MINIMUM_DOWNLOAD_QUEUE_SIZE')
    log_episode_errors: bool = Field(False, env='LOG_EPISODE_ERRORS')
    debug_api_calls: bool = Field(False, env='DEBUG_API_CALLS')

    class Config:
        env_file = ".env"  # optional: load from .env file
