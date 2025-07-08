import socket

# Get the local (private) IPv4 address
def get_local_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

# Path to your RAT script
file_path = "client.py"  # Change this to the actual script name

# Read and replace the IP
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'SERVER_IP =' in line and 'REPLACE WITH THE IPv4 OF THE COMPUTER YOUR ATTACKING FROM' in line:
        new_ip = get_local_ipv4()
        new_line = f'SERVER_IP = "{new_ip}"  # Automatically inserted\n'
        new_lines.append(new_line)
    else:
        new_lines.append(line)

# Overwrite the file with the updated IP
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"[+] IPv4 address inserted successfully: {get_local_ipv4()}")
