import toml

with open('config.toml', 'r') as f:
    config = toml.load(f)