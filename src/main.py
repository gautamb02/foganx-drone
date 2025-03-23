import argparse
from condifgreader import config

def main():
    parser = argparse.ArgumentParser(description="Read configuration file")
    parser.add_argument("--config", type=str, default="config.yml", help="Path to the config file")
    args = parser.parse_args()

    config_data = config.read_config(args.config)
    if config_data:
        print(config_data.network.wifi.SSID)

main()