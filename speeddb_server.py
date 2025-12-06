import socket
import threading
import json
import os
import traceback
from cryptography.fernet import Fernet
import base64
import hashlib
import sys

PASSWORD = "speed123"

# ============================================================
#                PATHS RELATIVE TO APP LOCATION
# ============================================================

if getattr(sys, "frozen", False):
    # When running as PyInstaller EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # When running as normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIRECTORY = os.path.join(BASE_DIR, "speeddb_data")
META_DIRECTORY = os.path.join(DB_DIRECTORY, "meta")

os.makedirs(DB_DIRECTORY, exist_ok=True)
os.makedirs(META_DIRECTORY, exist_ok=True)


def get_fernet():
    # Derive a 32-byte key from the PASSWORD using SHA-256
    key = hashlib.sha256(PASSWORD.encode("utf-8")).digest()
    # Fernet needs urlsafe base64-encoded 32-byte key
    return Fernet(base64.urlsafe_b64encode(key))


FERNET = get_fernet()


def meta_path(table):
    return os.path.join(META_DIRECTORY, f"{table}.meta.json")


def table_path(table):
    return os.path.join(DB_DIRECTORY, f"{table}.json")


def load_table(table):
    path = table_path(table)
    if not os.path.exists(path):
        return []

    # Read raw encrypted bytes
    with open(path, "rb") as f:
        encrypted = f.read().strip()
        if not encrypted:
            return []

    try:
        decrypted = FERNET.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))
    except Exception:
        traceback.print_exc()
        return []


def save_table(table, data):
    path = table_path(table)
    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted = FERNET.encrypt(plaintext)

    with open(path, "wb") as f:
        f.write(encrypted)


def load_meta(table):
    path = meta_path(table)
    if not os.path.exists(path):
        return {"columns": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_meta(table, meta):
    path = meta_path(table)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def list_tables():
    return [f[:-5] for f in os.listdir(DB_DIRECTORY) if f.endswith(".json")]


def send(conn, msg):
    """Force single line"""
    msg = msg.replace("\n", " ")
    conn.send((msg + "\n").encode("utf-8"))


def parse_where_clause(parts):
    if "WHERE" not in [p.upper() for p in parts]:
        return None

    uparts = [p.upper() for p in parts]
    idx = uparts.index("WHERE")

    clause = " ".join(parts[idx + 1:]).strip()
    if "=" not in clause:
        return None

    left, right = clause.split("=", 1)
    left = left.strip()
    right = right.strip()

    if right.startswith('"') and right.endswith('"'):
        right = right[1:-1]

    return (left, right)


def evaluate_condition(row, cond):
    if not cond:
        return False
    key, val = cond
    return key in row and str(row[key]) == str(val)


def handle_command_line(raw, authed_user):
    global PASSWORD

    parts = raw.split()
    cmd = parts[0].upper()

    # ------------------------
    # AUTH
    # ------------------------
    if cmd == "AUTH":
        if len(parts) < 3:
            return False, "ERROR Missing credentials"
        user = parts[1]
        pw = parts[2]
        if pw == PASSWORD:
            return True, f"OK AUTH_SUCCESS user={user}"
        return False, "ERROR Invalid password"

    # ------------------------
    # LIST_TABLES
    # ------------------------
    if cmd == "LIST_TABLES":
        return True, "OK " + json.dumps(list_tables())

    # ------------------------
    # CREATE_TABLE
    # ------------------------
    if cmd == "CREATE_TABLE":
        if len(parts) < 2:
            return False, "ERROR Missing table name"
        table = parts[1]
        cols = parts[2:]
        if os.path.exists(table_path(table)):
            return False, "ERROR Table exists"
        save_table(table, [])
        save_meta(table, {"columns": cols})
        return True, "OK TABLE_CREATED"

    # ------------------------
    # DROP_TABLE
    # ------------------------
    if cmd == "DROP_TABLE":
        if len(parts) < 2:
            return False, "ERROR Missing table"
        table = parts[1]
        try:
            os.remove(table_path(table))
        except:
            pass
        try:
            os.remove(meta_path(table))
        except:
            pass
        return True, "OK TABLE_DROPPED"

    # ------------------------
    # GET_TABLE
    # ------------------------
    if cmd == "GET_TABLE":
        if len(parts) < 2:
            return False, "ERROR Missing table"
        table = parts[1]
        rows = load_table(table)
        return True, "OK " + json.dumps(rows)

    # ------------------------
    # INSERT
    # ------------------------
    if cmd == "INSERT":
        if len(parts) < 3:
            return False, "ERROR Usage: INSERT table {json}"

        table = parts[1]
        json_str = raw.split(" ", 2)[2]

        try:
            row = json.loads(json_str)
        except Exception as e:
            return False, f"ERROR Invalid JSON: {e}"

        rows = load_table(table)
        rows.append(row)
        save_table(table, rows)
        return True, "OK INSERTED"

    # ------------------------
    # DELETE_ROW
    # ------------------------
    if cmd == "DELETE_ROW":
        if len(parts) < 2:
            return False, "ERROR Missing table"
        table = parts[1]
        cond = parse_where_clause(parts)
        rows = load_table(table)
        rows = [r for r in rows if not evaluate_condition(r, cond)]
        save_table(table, rows)
        return True, "OK ROW_DELETED"

    # ------------------------
    # HELP
    # ------------------------
    if cmd == "HELP":
        return True, "OK COMMANDS AUTH LIST_TABLES GET_TABLE INSERT DELETE_ROW"

    return False, "ERROR Unknown command"


def handle_client(conn, addr):
    print(f"[Client connected] {addr}")

    authed_user = None
    authed = False

    try:
        while True:
            data = conn.recv(4096).decode("utf-8")
            if not data:
                break

            for raw in data.splitlines():
                raw = raw.strip()
                if not raw:
                    continue

                print("[Client says]", raw)

                parts = raw.split()
                cmd = parts[0].upper()

                if cmd == "AUTH":
                    ok, resp = handle_command_line(raw, authed_user)
                    if ok:
                        authed = True
                    send(conn, resp)
                    continue

                if not authed:
                    send(conn, "ERROR Not authenticated")
                    continue

                ok, resp = handle_command_line(raw, authed_user)
                send(conn, resp)

    except Exception as e:
        print("error:", e)

    finally:
        print("[Client disconnected]")
        conn.close()


def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 6969))
    s.listen(5)

    print("SpeedDB running on port 6969")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start_server()
