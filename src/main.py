import argparse
from configreader import config
from logger.log import logger

logger.info("Starting application")

def main():
    parser = argparse.ArgumentParser(description="Read configuration file")
    parser.add_argument("--config", type=str, default="config.yml", help="Path to the config file")
    args = parser.parse_args()

    config_data = config.read_config(args.config)
    if config_data:
        logger.info("Config Loaded Successfully.")
    else:
        logger.fatal("Error reading in config.")
        return

main()