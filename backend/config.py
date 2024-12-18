import toml
from loguru import logger

with open('config.toml', 'r') as f:
    config = toml.load(f)

logger.info(f"Config loaded: {config}")