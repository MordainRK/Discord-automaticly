import json
import os
import sys
import time
import requests

# --- Konstanta untuk konfigurasi ---
MESSAGE_DELAY_SECONDS = 10  # delay antar channel biar aman

def load_config():
    """Ambil config dari Secrets (ENV DISCORD_CONFIG) atau dari file config.json lokal"""
    config_env = os.getenv("DISCORD_CONFIG")
    if config_env:
        try:
            return json.loads(config_env)
        except json.JSONDecodeError:
            print("[X] Error: Format JSON di Secrets DISCORD_CONFIG tidak valid.")
            sys.exit(1)
    elif os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("[X] Error: Format JSON di file config.json tidak valid.")
            sys.exit(1)
    else:
        print("[X] Error: Tidak ada config.json dan ENV DISCORD_CONFIG tidak ditemukan.")
        sys.exit(1)

def load_last_index(filepath):
    """Membuka dan membaca file indeks terakhir"""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r") as f:
            return int(f.read().strip())
    except (ValueError, TypeError):
        return 0

def save_next_index(filepath, current_index, total_accounts):
    """Simpan indeks berikutnya (rolling round robin)"""
    next_index = (current_index + 1) % total_accounts
    with open(filepath, "w") as f:
        f.write(str(next_index))
    print(f"[*] Indeks diperbarui → eksekusi berikutnya mulai dari akun index {next_index}")

def send_messages_for_account(account, index):
    """Mengirim semua pesan dari 1 akun ke semua channel"""
    token = account.get("token")
    channels = account.get("channels", [])

    if not token or not channels:
        print(f"[X] Akun index {index} dilewati (token / channel kosong).")
        return

    headers = {"Authorization": token}

    print(f"\n--- [Akun index {index}] Token ...{token[-4:]} ---")

    for ch in channels:
        channel_id = ch.get("id")
        message_content = ch.get("message")

        if not channel_id or not message_content:
            print(f"[!] Channel kosong dilewati (akun index {index})")
            continue

        try:
            response = requests.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json={"content": message_content},
                timeout=15
            )

            if response.status_code in [200, 201]:
                print(f"[✓] Berhasil kirim ke channel {channel_id}")
            else:
                print(f"[X] Gagal kirim ke channel {channel_id} | Status {response.status_code} | Respon: {response.text}")

            time.sleep(MESSAGE_DELAY_SECONDS)

        except requests.exceptions.RequestException as e:
            print(f"[X] Error koneksi: {e}")

def main():
    if len(sys.argv) < 2:
        print("Penggunaan: python bot_sender.py <last_index.txt>")
        sys.exit(1)

    last_index_filepath = sys.argv[1]

    config = load_config()
    accounts = config.get("accounts", [])

    if not accounts:
        print("[X] Tidak ada akun di config.")
        sys.exit(1)

    last_index = load_last_index(last_index_filepath)
    current_index = last_index % len(accounts)

    print(f"[*] Total akun: {len(accounts)}")
    print(f"[*] Last index: {last_index} → Jalankan akun index {current_index}")

    account_to_use = accounts[current_index]
    send_messages_for_account(account_to_use, current_index)

    save_next_index(last_index_filepath, current_index, len(accounts))
    print("\n[+] Selesai.")

if __name__ == "__main__":
    main()
