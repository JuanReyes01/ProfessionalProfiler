# config.py
from pydantic import BaseModel
from typing import Dict
import yaml


class LoggingConfig(BaseModel):
    level: str
    file_path: str
    max_size: int
    backup_count: int
    format: str


class Config(BaseModel):
    logging: LoggingConfig
    crawler: Dict[str, int | str]
    fuzzy: Dict[str, float | str]


def load_config(config_path: str = "config.yaml") -> Config:
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    return Config(**raw_config)
