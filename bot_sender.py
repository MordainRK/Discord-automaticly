import os
import sys
import json
import time
import requests

MESSAGE_DELAY_SECONDS = 7  # jeda antar pesan biar aman

def load_config():
    """Baca config dari GitHub Secret"""
    secret = os.environ.get("DISCORD_CONFIG")
    if not secret:
        print("[X] Secret DISCORD_CONFIG tidak ditemukan!")
        sys.exit(1)
    try:
        return json.loads(secret)
    except json.JSONDecodeError as e:
        print(f"[X] Error parsing JSON di DISCORD_CONFIG: {e}")
        sys.exit(1)

def load_last_index(filepath):
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_next_index(filepath, current_index, total_accounts):
    next_index = (current_index + 1) % total_accounts
    with open(filepath, "w") as f:
        f.write(str(next_index))
    print(f"[*] Indeks disimpan. Next run mulai dari {next_index}")

def send_messages(account):
    token = account.get("token")
    channels = account.get("channels", [])

    if not token or not channels:
        print("[X] Akun dilewati karena token / channel kosong.")
        return

    headers = {"Authorization": token}
    print(f"\n--- Akun Token: ...{token[-4:]} ---")

    for ch in channels:
        cid = ch.get("id")
        msg = ch.get("message")
        if not cid or not msg:
            continue

        try:
            r = requests.post(
                f"https://discord.com/api/v9/channels/{cid}/messages",
                headers=headers,
                json={"content": msg},
                timeout=15
            )
            if r.status_code in [200, 201]:
                print(f"[✓] Berhasil ke {cid}")
            else:
                print(f"[X] Gagal {cid} | {r.status_code} | {r.text}")

        except Exception as e:
            print(f"[X] Error {cid}: {e}")

        time.sleep(MESSAGE_DELAY_SECONDS)

def main():
    if len(sys.argv) < 2:
        print("Usage: python bot_sender.py <last_index.txt>")
        sys.exit(1)

    last_index_file = sys.argv[1]
    config = load_config()
    accounts = config.get("accounts", [])

    if not accounts:
        print("[X] Tidak ada akun ditemukan di config.")
        sys.exit(1)

    last_index = load_last_index(last_index_file)
    current_index = last_index % len(accounts)

    print(f"[*] Total akun: {len(accounts)} | Mulai dari index {current_index}")

    send_messages(accounts[current_index])

    save_next_index(last_index_file, current_index, len(accounts))
    print("[+] Selesai.")

if __name__ == "__main__":
    main()
