import json
import os
import sys
import time
import requests

# --- Konstanta untuk konfigurasi ---
# Delay dalam detik antar pengiriman pesan ke channel yang berbeda
MESSAGE_DELAY_SECONDS = 10

def load_config(filepath):
    """Membuka dan memuat file konfigurasi JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[X] Error: File konfigurasi tidak ditemukan di '{filepath}'")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[X] Error: Format JSON di '{filepath}' tidak valid.")
        sys.exit(1)

def load_last_index(filepath):
    """Membuka dan membaca file yang berisi indeks terakhir yang digunakan."""
    if not os.path.exists(filepath):
        return 0  # Jika file tidak ada, mulai dari indeks 0
    
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
            return int(content)
    except (ValueError, TypeError):
        # Jika file kosong atau berisi teks yang bukan angka, anggap 0
        return 0

def save_next_index(filepath, current_index):
    """Menyimpan indeks berikutnya untuk eksekusi selanjutnya."""
    next_index = current_index + 1
    with open(filepath, "w") as f:
        f.write(str(next_index))
    print(f"[*] Indeks diperbarui. Eksekusi berikutnya akan mulai dari indeks: {next_index}")

def send_messages_for_account(account):
    """Mengirim semua pesan yang dikonfigurasi untuk satu akun."""
    token = account.get("token")
    channels = account.get("channels", [])
    
    if not token or not channels:
        print("[X] Peringatan: Akun dilewati karena token atau channel tidak ada.")
        return

    headers = {"Authorization": token}
    
    print(f"\n--- Menggunakan Akun (Token berakhir dengan: ...{token[-4:]}) ---")

    for ch in channels:
        channel_id = ch.get("id")
        message_content = ch.get("message")
        
        if not channel_id or not message_content:
            print(f"[X] Peringatan: Channel dalam akun ...{token[-4:]} dilewati karena ID atau pesan kosong.")
            continue
            
        try:
            response = requests.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json={"content": message_content},
                timeout=15 # Timeout untuk mencegah skrip menggantung
            )
            
            if response.status_code == 200:
                print(f"[✓] Pesan berhasil dikirim ke channel {channel_id}")
            else:
                print(f"[X] Gagal mengirim ke channel {channel_id} | Status: {response.status_code} | Respon: {response.text}")

            # Beri jeda antar pengiriman pesan
            time.sleep(MESSAGE_DELAY_SECONDS)
            
        except requests.exceptions.RequestException as e:
            print(f"[X] Terjadi error saat menghubungi Discord untuk channel {channel_id}: {e}")
        except Exception as e:
            print(f"[X] Terjadi error yang tidak diketahui: {e}")

def main():
    """Fungsi utama untuk menjalankan bot."""
    if len(sys.argv) < 3:
        print("Penggunaan: python bot_sender.py <config.json> <last_index.txt>")
        sys.exit(1)

    config_filepath = sys.argv[1]
    last_index_filepath = sys.argv[2]

    # 1. Muat konfigurasi dan data yang diperlukan
    config = load_config(config_filepath)
    accounts = config.get("accounts", [])
    
    if not accounts:
        print("[X] Error: Tidak ada akun yang ditemukan di file konfigurasi.")
        sys.exit(1)

    # 2. Tentukan akun mana yang akan digunakan
    last_index = load_last_index(last_index_filepath)
    num_accounts = len(accounts)
    
    # Gunakan modulo (%) untuk memastikan indeks selalu valid dan berputar (round-robin)
    current_account_index = last_index % num_accounts
    
    print(f"[*] Memulai dari indeks tersimpan: {last_index}")
    print(f"[*] Total akun: {num_accounts}. Menggunakan akun ke-{current_account_index + 1}.")
    
    account_to_use = accounts[current_account_index]

    # 3. Kirim pesan menggunakan akun yang dipilih
    send_messages_for_account(account_to_use)

    # 4. Simpan indeks untuk eksekusi berikutnya
    save_next_index(last_index_filepath, last_index)
    
    print("\n[+] Selesai.")

if __name__ == "__main__":
    main()
