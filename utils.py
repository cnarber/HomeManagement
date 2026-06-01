import socket
from getmac import get_mac_address

def get_user_from_ip(ip_address):
    comp_name = get_hostname_from_ip(ip_address)
    mac_address = get_mac_address(ip=ip_address)


    print(comp_name, mac_address)
    return ip_address

def get_hostname_from_ip(ip_address):
    """
    Performs a reverse DNS lookup to get the hostname for a given IP address.

    Args:
        ip_address (str): The IP address (e.g., "8.8.8.8", "192.168.1.1").

    Returns:
        str: The hostname if found, otherwise an error message or None.
    """
    try:
        # socket.gethostbyaddr returns a tuple:
        # (hostname, aliaslist, ipaddrlist)
        hostname_info = socket.gethostbyaddr(ip_address)
        return hostname_info[0] # The primary hostname is the first element
    except socket.herror:
        return "No hostname found for this IP address (DNS lookup failed)."
    except socket.timeout:
        return "Reverse DNS lookup timed out."
    except Exception as e:
        return f"An error occurred: {e}"


if __name__=="__main__":
    ip_address = "10.0.0.40"  # Replace with the target IP address
    mac_address = get_mac_address(ip=ip_address)
    print(f"MAC address for {ip_address}: {mac_address}")
    print(get_hostname_from_ip(ip_address))
