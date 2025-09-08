import json
import os
import sys
import time
import requests
from datetime import datetime

# --- Konstanta untuk konfigurasi ---
MESSAGE_DELAY_SECONDS = 10  # Jeda antar pesan

def load_config(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[X] File konfigurasi tidak ditemukan: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[X] Format JSON salah di file: {filepath}")
        sys.exit(1)

def load_last_index(filepath):
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_next_index(filepath, current_index, num_accounts):
    next_index = (current_index + 1) % num_accounts
    with open(filepath, "w") as f:
        f.write(str(next_index))
    print(f"[*] Indeks diperbarui. Next run mulai dari index: {next_index}")

def send_messages_for_account(account, account_index):
    token = account.get("token")
    channels = account.get("channels", [])
    
    if not token or not channels:
        print(f"[X] Akun index {account_index} dilewati (token/channels kosong)")
        return

    headers = {"Authorization": f"{token}"}
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔑 Akun index {account_index} (Token ...{token[-4:]})")

    for ch in channels:
        channel_id = ch.get("id")
        message_content = ch.get("message")
        
        if not channel_id or not message_content:
            print(f"[!] Channel dilewati (ID/Pesan kosong) di akun {account_index}")
            continue

        try:
            response = requests.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json={"content": message_content},
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Berhasil -> Channel {channel_id}")
            elif response.status_code == 401:
                print(f"❌ Token Invalid -> Akun {account_index}")
            elif response.status_code == 403:
                print(f"❌ Tidak ada izin kirim -> Channel {channel_id}")
            elif response.status_code == 429:
                retry_after = response.json().get("retry_after", 5)
                print(f"⚠️ Rate Limit -> Tunggu {retry_after} detik")
                time.sleep(retry_after)
            else:
                print(f"❌ Gagal -> Status {response.status_code}, Respon: {response.text}")

            time.sleep(MESSAGE_DELAY_SECONDS)

        except requests.exceptions.RequestException as e:
            print(f"[X] Error request ke Discord: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python bot_sender.py <config.json> <last_index.txt>")
        sys.exit(1)

    config_filepath = sys.argv[1]
    last_index_filepath = sys.argv[2]

    config = load_config(config_filepath)
    accounts = config.get("accounts", [])

    if not accounts:
        print("[X] Tidak ada akun di config.json")
        sys.exit(1)

    last_index = load_last_index(last_index_filepath)
    num_accounts = len(accounts)

    current_account_index = last_index % num_accounts
    print(f"[*] Last index: {last_index}, Total akun: {num_accounts}, Run sekarang: index {current_account_index}")

    account_to_use = accounts[current_account_index]
    send_messages_for_account(account_to_use, current_account_index)

    save_next_index(last_index_filepath, current_account_index, num_accounts)

    print("\n[+] Selesai.\n")

if __name__ == "__main__":
    main()
