from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import random
import vlc
import socket
import json
import time
import threading
import speeddb_server
import os
import sys

# ============================================================
#                PATHS RELATIVE TO APP LOCATION
# ============================================================

if getattr(sys, "frozen", False):
    # When running as PyInstaller EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # When running as normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLIPS_DIR = os.path.join(BASE_DIR, "clips")
AUDIO_DIR = os.path.join(CLIPS_DIR, "audio")

# ============================================================
#                   CONFIG
# ============================================================

CORRECT_ROOT_PASSWORD = "myroot123"

SPEED_MAD_CLIPS = [
    os.path.join(CLIPS_DIR, "speed_mad1.mp4"),
    os.path.join(CLIPS_DIR, "speed_mad2.mp4"),
    os.path.join(CLIPS_DIR, "speed_mad3.mp4"),
    os.path.join(CLIPS_DIR, "speed_mad4.mp4"),
    os.path.join(CLIPS_DIR, "speedksi1.mp4"),
    os.path.join(CLIPS_DIR, "quitmusic.mp4"),
    os.path.join(CLIPS_DIR, "aaah.mp4"),
    os.path.join(CLIPS_DIR, "imgay2.mp4"),
    os.path.join(CLIPS_DIR, "uabeech.mp4"),
    os.path.join(CLIPS_DIR, "letsgo.mp4"),
    os.path.join(CLIPS_DIR, "notscary.mp4"),
    os.path.join(CLIPS_DIR, "15yrold.mp4"),
    os.path.join(CLIPS_DIR, "yougonnaloveit.mp4"),
]

SPEED_IM_GAY_CLIP = os.path.join(CLIPS_DIR, "speed_im_gay.mp4")

CHECKPOINTS = [1100, 4700, 8900, 11000]
CHECKPOINT_DIALOGUE = [
    "what's up you got a million?",
    "what's up? tell me",
    "what's up?",
    "WHAT?",
]

SPEED_ERROR_SCREAMS = [
    os.path.join(AUDIO_DIR, "abcd.mp3"),
    os.path.join(AUDIO_DIR, "bark.mp3"),
    os.path.join(AUDIO_DIR, "bark2.mp3"),
    os.path.join(AUDIO_DIR, "fuck.mp3"),
    os.path.join(AUDIO_DIR, "fuck2.mp3"),
    os.path.join(AUDIO_DIR, "getoffthegame.mp3"),
    os.path.join(AUDIO_DIR, "gettingoverit.mp3"),
    os.path.join(AUDIO_DIR, "laugh.mp3"),
    os.path.join(AUDIO_DIR, "mad.mp3"),
    os.path.join(AUDIO_DIR, "minors.mp3"),
    os.path.join(AUDIO_DIR, "no.mp3"),
    os.path.join(AUDIO_DIR, "scream.mp3"),
    os.path.join(AUDIO_DIR, "soyou.mp3"),
    os.path.join(AUDIO_DIR, "wtf.mp3"),
]


# ============================================================
#                   VIDEO / AUDIO
# ============================================================

def play_video(path, callback=None):
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(path)
    player.set_media(media)
    player.play()

    def check_end():
        state = player.get_state()
        if state in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
            try:
                player.stop()
                player.release()
                instance.release()
            except:
                pass
            if callback:
                callback()
        else:
            root.after(200, check_end)

    root.after(200, check_end)


def play_sound(path):
    instance = vlc.Instance("--novideo")
    player = instance.media_player_new()
    media = instance.media_new(path)
    player.set_media(media)
    player.play()

    def check():
        if player.get_state() in (vlc.State.Ended, vlc.State.Error):
            try:
                player.stop()
                player.release()
                instance.release()
            except:
                pass
        else:
            root.after(150, check)

    root.after(150, check)


# ============================================================
#                "I'M GAY" VISUAL NOVEL SEQUENCE
# ============================================================

def vn_popup(response_text, callback):
    popup = tk.Toplevel(root)
    popup.title("Dialogue")
    popup.geometry("360x180")
    popup.configure(bg="#0b0f18")
    popup.resizable(False, False)
    popup.grab_set()

    tk.Label(
        popup, text='Speed: "guess what ?"',
        bg="#0b0f18", fg="white", font=("Segoe UI", 12)
    ).pack(pady=15)

    tk.Button(
        popup, text=f'You: "{response_text}"',
        width=30,
        command=lambda: (popup.destroy(), callback()),
        bg="#16a34a", fg="white", relief="flat"
    ).pack(pady=10)


def play_im_gay_sequence():
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(SPEED_IM_GAY_CLIP)
    player.set_media(media)
    player.play()

    checkpoint_index = 0

    def check_video():
        nonlocal checkpoint_index
        time_ms = player.get_time()

        if checkpoint_index < len(CHECKPOINTS) and time_ms >= CHECKPOINTS[checkpoint_index]:
            player.pause()
            dialogue = CHECKPOINT_DIALOGUE[checkpoint_index]

            def resume_after():
                player.play()
                root.after(200, check_video)

            vn_popup(dialogue, resume_after)
            checkpoint_index += 1
            return

        if player.get_state() in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
            try:
                player.stop()
                player.release()
                instance.release()
            except:
                pass
            switch_to(login_frame)
        else:
            root.after(150, check_video)

    root.after(200, check_video)


# ============================================================
#                ERROR POPUPS
# ============================================================

def show_wrong_root_popup():
    popup = tk.Toplevel(root)
    popup.title("Root Key Error")
    popup.geometry("420x170")
    popup.configure(bg="#0b0f18")
    popup.resizable(False, False)
    popup.grab_set()

    tk.Label(
        popup, text="Wrong SpeedDB Root Key.",
        bg="#0b0f18", fg="white", font=("Segoe UI", 12)
    ).pack(pady=20)

    btn_frame = tk.Frame(popup, bg="#0b0f18")
    btn_frame.pack()

    tk.Button(
        btn_frame, text="My bad, imma retry",
        width=18, bg="#16a34a", fg="white", relief="flat",
        command=lambda: popup.destroy()
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        btn_frame, text="Guess what, I don't care",
        width=18, bg="#dc2626", fg="white", relief="flat",
        command=lambda: (popup.destroy(), play_im_gay_sequence())
    ).grid(row=0, column=1, padx=5)


def show_wrong_db_popup():
    popup = tk.Toplevel(root)
    popup.title("SpeedDB Failed")
    popup.geometry("420x170")
    popup.configure(bg="#0b0f18")
    popup.resizable(False, False)
    popup.grab_set()

    tk.Label(
        popup, text="SpeedDB could not connect.",
        bg="#0b0f18", fg="white", font=("Segoe UI", 12)
    ).pack(pady=20)

    btn_frame = tk.Frame(popup, bg="#0b0f18")
    btn_frame.pack()

    tk.Button(
        btn_frame, text="My bad, imma retry",
        width=18, bg="#16a34a", fg="white", relief="flat",
        command=lambda: popup.destroy()
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        btn_frame, text="Guess what, I don't care",
        width=18, bg="#dc2626", fg="white", relief="flat",
        command=lambda: (popup.destroy(), play_im_gay_sequence())
    ).grid(row=0, column=1, padx=5)


# ============================================================
#                       GUI SETUP
# ============================================================

root = tk.Tk()
root.title("SpeedDB Access Panel")
root.geometry("650x750")
root.configure(bg="#0b0f18")

icon_path = os.path.join(BASE_DIR, "speed_icon.ico")
try:
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
except Exception as e:
    print("Could not set window icon:", e)



def make_input(parent, label):
    tk.Label(parent, text=label, bg="#0b0f18", fg="#e0e0e0").pack(anchor="w", padx=20)
    entry = tk.Entry(
        parent,
        width=60,
        bg="#b0c5f0",
        fg="#111827",
        relief="solid",
        borderwidth=1,
        insertbackground="#111827"
    )
    entry.pack(padx=20, pady=6, ipady=4)
    return entry


# ---------------- LOGIN SCREEN ----------------

login_frame = tk.Frame(root, bg="#0b0f18")
login_frame.pack(expand=True, fill="both")

try:
    speed_face_path = os.path.join(CLIPS_DIR, "speed_face.png")
    speed_img_raw = Image.open(speed_face_path)
    speed_img_raw = speed_img_raw.resize((500, 220), Image.Resampling.LANCZOS)
    speed_img = ImageTk.PhotoImage(speed_img_raw)
    speed_label = tk.Label(login_frame, image=speed_img, bg="#0b0f18")
    speed_label.image = speed_img
    speed_label.pack(pady=(10, 5))
except Exception as e:
    print("Failed to load speed_face.png:", e)

tk.Label(
    login_frame, text="SpeedDB",
    font=("Segoe UI", 26, "bold"),
    fg="#ff0040", bg="#0b0f18"
).pack(pady=15)

url_entry = make_input(login_frame, "SpeedDB URL:")
key_entry = make_input(login_frame, "SpeedDB Key:")
table_entry = make_input(login_frame, "SpeedDB Table:")
root_pass_entry = make_input(login_frame, "SpeedDB Root Key:")
root_pass_entry.config(show="*")

# Prefill sensible defaults for local use
url_entry.insert(0, "localhost")
key_entry.insert(0, "speed123")

status_label = tk.Label(login_frame, text="", bg="#0b0f18", fg="#ccc")
status_label.pack(pady=5)


# ---------------- DATA SCREEN ----------------

data_frame = tk.Frame(root, bg="#0b0f18")

table_view = ttk.Treeview(data_frame, show="headings", height=14)

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    background="#0f0f14",
    foreground="#00eaff",
    rowheight=26,
    fieldbackground="#0f0f14",
    bordercolor="#222",
    borderwidth=1
)
style.configure(
    "Treeview.Heading",
    background="#1a1a1a",
    foreground="#00eaff",
    font=("Segoe UI", 11, "bold")
)
style.map("Treeview", background=[("selected", "#2563eb")])

table_view.pack(padx=12, pady=10, fill="both")

response_box = tk.Text(
    data_frame,
    width=80, height=8,
    bg="#113322",
    fg="#9FFFCB",
    relief="solid",
    borderwidth=1
)
response_box.pack(padx=10, pady=10)

cmd_frame = tk.Frame(data_frame, bg="#0b0f18")
cmd_frame.pack(pady=8)

cmd_entry = tk.Entry(cmd_frame, width=55, bg="#222", fg="white")
cmd_entry.grid(row=0, column=0, padx=5)


# ============================================================
#                SOCKET + COMMAND HANDLING
# ============================================================

speed_sock = None


def close_socket():
    global speed_sock
    try:
        if speed_sock:
            speed_sock.close()
    except:
        pass
    speed_sock = None


def recv_line(sock):
    buf = ""
    while True:
        chunk = sock.recv(4096).decode("utf-8")
        if not chunk:
            break
        buf += chunk
        if "\n" in chunk:
            break
    return buf.strip()


def update_table(rows):
    table_view.delete(*table_view.get_children())

    if not rows:
        table_view["columns"] = []
        return

    cols = list(rows[0].keys())
    table_view["columns"] = cols

    for c in cols:
        table_view.heading(c, text=c)
        table_view.column(c, width=140)

    for r in rows:
        table_view.insert("", "end", values=[r.get(c, "") for c in cols])


def send_command(cmd):
    global speed_sock

    try:
        speed_sock.send((cmd + "\n").encode())
        resp = recv_line(speed_sock)

        response_box.insert("end", f"> {cmd}\n{resp}\n\n")
        response_box.see("end")
        if resp.upper().startswith("ERROR"):
            play_sound(random.choice(SPEED_ERROR_SCREAMS))

        if cmd.upper().startswith("GET_TABLE") and resp.startswith("OK "):
            try:
                rows = json.loads(resp[3:].strip())
            except:
                rows = []
            update_table(rows)

    except Exception as e:
        response_box.insert("end", f"Error sending command: {e}\n")
        response_box.see("end")
        close_socket()


def on_send():
    c = cmd_entry.get().strip()
    if c:
        send_command(c)
    cmd_entry.delete(0, "end")


tk.Button(
    cmd_frame, text="Send",
    bg="#16a34a", fg="white",
    relief="flat", command=on_send
).grid(row=0, column=1, padx=5)

# Hit Enter in the command box to send
cmd_entry.bind("<Return>", lambda event: on_send())


tk.Button(
    data_frame, text="Back",
    bg="#ccc", fg="#000",
    command=lambda: (close_socket(), switch_to(login_frame))
).pack(pady=12)


def switch_to(frame):
    login_frame.pack_forget()
    data_frame.pack_forget()
    frame.pack(fill="both", expand=True)


# ============================================================
#                     CONNECT TO SERVER
# ============================================================

def attempt_connection():
    if root_pass_entry.get().strip() != CORRECT_ROOT_PASSWORD:
        play_video(random.choice(SPEED_MAD_CLIPS), callback=show_wrong_root_popup)
        return

    host = url_entry.get().strip()
    key = key_entry.get().strip()
    table = table_entry.get().strip()

    if not (host and key and table):
        status_label.config(text="Fill all fields!")
        return

    host = host.replace("http://", "").replace("https://", "").split("/")[0]

    global speed_sock
    try:
        speed_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        speed_sock.connect((host, 6969))

        speed_sock.send(f"AUTH speed {key}\n".encode())
        auth = recv_line(speed_sock)

        if "AUTH_SUCCESS" not in auth:
            raise Exception(auth)

        speed_sock.send(f"GET_TABLE {table}\n".encode())
        resp = recv_line(speed_sock)

        if resp.startswith("OK "):
            try:
                rows = json.loads(resp[3:].strip())
            except:
                rows = []
        else:
            rows = []

        update_table(rows)

        switch_to(data_frame)
        response_box.insert("end", f"Connected to {host}\n\n")
        response_box.see("end")

    except Exception as e:
        close_socket()
        response_box.insert("end", f"Connection failed: {e}\n")
        response_box.see("end")
        play_video(random.choice(SPEED_MAD_CLIPS), callback=show_wrong_db_popup)


# Login "Connect" button
tk.Button(
    login_frame, text="Connect",
    bg="#16a34a", fg="white",
    relief="flat",
    width=20, pady=4,
    command=attempt_connection
).pack(pady=15)

# Hit Enter in any login field to connect
for entry in (url_entry, key_entry, table_entry, root_pass_entry):
    entry.bind("<Return>", lambda event: attempt_connection())


# ============================================================
#                START INTERNAL SPEEDDB SERVER
# ============================================================

def start_speeddb_server():
    def run_server():
        print("[SpeedDB] starting internal server thread...")
        try:
            speeddb_server.start_server()
        except Exception as e:
            print("[SpeedDB] server thread crashed:", repr(e))

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    return t


start_speeddb_server()
root.mainloop()
