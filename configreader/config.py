import yaml
from dataclasses import dataclass
from typing import Optional

@dataclass
class Wifi:
    SSID: str
    Password: str

@dataclass
class Network:
    wifi: Wifi

@dataclass
class Config:
    network: Network

def read_config(file_path):
    """Reads a YAML file and returns it as a dataclass object."""
    try:
        with open(file_path, 'r') as file:
            config_dict = yaml.safe_load(file)
            return Config(network=Network(wifi=Wifi(**config_dict['network']['wifi'])))
    except Exception as e:
        print(f"Error reading the config file: {e}")
        return None

