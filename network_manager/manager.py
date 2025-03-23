import subprocess

import subprocess
# import yaml
import platform
import re

class TelloNetworkManager:
    def __init__(self,SSID = "Telephonic",Key= "00000000"):
        self.ssid = SSID
        self.password = Key
        # self.config_file = config_file
        self.interface = self._get_wifi_interface()
        
    def _get_wifi_interface(self) -> str | None:
        """Detects the active Wi-Fi interface name across Linux, Windows, and macOS."""
        system = platform.system()
        
        if system == "Linux":
            return self._get_linux_wifi_interface()
        elif system == "Windows":
            return self._get_windows_wifi_interface()
        elif system == "Darwin":  # macOS
            return self._get_macos_wifi_interface()
        else:
            print(f"Unsupported operating system: {platform.system()}" )
            return None
    
    def _get_linux_wifi_interface(self) -> str | None:
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,TYPE", "device"],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                device, dev_type = line.split(":")
                if dev_type == "wifi":
                    return device
        except subprocess.CalledProcessError:
            pass
        return None
    
    def _get_windows_wifi_interface(self) -> str | None:
        try:
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"],
                                    capture_output=True, text=True, check=True)
            
            for line in result.stdout.splitlines():
                if "Name" in line:  # Look for the interface name
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[1].strip()  # Extract interface name safely
        except subprocess.CalledProcessError:
            pass
        return None
    
    def _get_macos_wifi_interface(self) -> str | None:
        try:
            result = subprocess.run(["networksetup", "-listallhardwareports"],
                                    capture_output=True, text=True, check=True)
            matches = re.findall(r"Hardware Port: Wi-Fi\nDevice: (\S+)", result.stdout)
            return matches[0] if matches else None
        except subprocess.CalledProcessError:
            pass
        return None
    
    # def _load_config(self) -> tuple[str | None, str | None]:
    #     """Loads Wi-Fi credentials from the configuration file."""
    #     try:
    #         with open(self.config_file, 'r') as file:
    #             config = yaml.safe_load(file)
    #             wifi_config = config.get('wifi', {})
    #             return wifi_config.get('ssid'), wifi_config.get('password')
    #     except Exception as e:
    #         logger.fatal(f"Error loading config: {e}")
    #         return None, None
    
    def connect_to_network(self) -> bool:
        """Connects to the Wi-Fi network."""
        if not self.interface:
            print("No active Wi-Fi interface found.")
            return False
        if not self.ssid or not self.password:
            print("SSID or password not found in the configuration file.")
            return False
        try:
            system = platform.system()
            if system == "Linux":
                subprocess.run(["nmcli", "d", "wifi", "connect", self.ssid, "password", self.password], check=True)
            elif system == "Windows":
                subprocess.run(["netsh", "wlan", "connect", "name=", self.ssid], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["networksetup", "-setairportnetwork", self.interface, self.ssid, self.password], check=True)
            else:
                print(f"Unsupported operating system: {system}")
                return False
            print(f"Successfully connected to {self.ssid}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to connect to {self.ssid}: {e}")
            return False
    
    def disconnect_from_network(self) -> bool:
        """Disconnects from the current Wi-Fi network."""
        if not self.interface:
            print("No active Wi-Fi interface found.")
            return False
        try:
            system = platform.system()
            if system == "Linux":
                subprocess.run(["nmcli", "dev", "disconnect", self.interface], check=True)
            elif system == "Windows":
                subprocess.run(["netsh", "wlan", "disconnect"], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["networksetup", "-setairportpower", self.interface, "off"], check=True)
            else:
                print(f"Unsupported operating system: {system}")
                return False
            print(f"Disconnected from Wi-Fi on {self.interface}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to disconnect from Wi-Fi: {e}")
            return False
if __name__ == '__main__':

    wifi = TelloNetworkManager("Telephonic", "00000000")  # Replace with actual network and password
    if(wifi.connect_to_network()):
        print("Connected")
    else:
        print("Error occured while connecting")
    
    wifi.disconnect_from_network()

