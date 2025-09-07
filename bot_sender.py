import json
import os
import sys
import time
import requests

if len(sys.argv) < 3:
    print("Usage: python bot_sender.py <config.json> <last_index.txt>")
    sys.exit(1)

config_file = sys.argv[1]
last_index_file = sys.argv[2]

# Load config
with open(config_file, "r") as f:
    config = json.load(f)

tokens = [acc["token"] for acc in config["accounts"]]
channels_per_account = [acc["channels"] for acc in config["accounts"]]

# Load last index
if os.path.exists(last_index_file):
    with open(last_index_file, "r") as f:
        try:
            last_index = int(f.read().strip())
        except:
            last_index = 0
else:
    last_index = 0

print(f"Start from index {last_index}")

# Pick token
index = last_index % len(tokens)
token = tokens[index]
channels = channels_per_account[index]

headers = {"Authorization": token}

success = True
for ch in channels:
    try:
        r = requests.post(
            f"https://discord.com/api/v9/channels/{ch['id']}/messages",
            headers=headers,
            json={"content": ch["message"]},
        )
        if r.status_code == 200:
            print(f"[✓] Sent to {ch['id']}")
        else:
            print(f"[X] Failed {ch['id']} : {r.status_code}")
            success = False
        time.sleep(10)  # delay antar channel
    except Exception as e:
        print("Error:", e)
        success = False

# Update index (selalu naik, walau gagal)
new_index = (index + 1) % len(tokens)
with open(last_index_file, "w") as f:
    f.write(str(new_index))
print(f"Updated last_index -> {new_index}")
