from socket import gethostbyname


def get_ip_address():
    """Get the machine's LAN IP address or fallback to localhost."""
    try:
       # Replace 'localhost' with any hostname you want to resolve
        hostname = 'host.docker.internal'

        # Get the IP address for the hostname
        ip_address = gethostbyname(hostname)
        return ip_address
    
    except Exception as e:
        return "127.0.0.1"
