import requests
import time
import os
from colorama import init, Fore
from datetime import datetime

init(autoreset=True)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print(Fore.CYAN + "="*55)
    print(Fore.CYAN + "      Advanced Discord DM Cleaner Tool")
    print(Fore.CYAN + "        Developed by: qpqn  |  Got")
    print(Fore.CYAN + "="*55)

def get_user_info(token):
    url = "https://discord.com/api/v9/users/@me"
    headers = {"Authorization": token}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def ask_token():
    while True:
        token = input(Fore.YELLOW + "[?] Enter your Discord Token: ").strip()
        user = get_user_info(token)
        if user:
            print(Fore.GREEN + f"[+] Token is valid! Logged in as {user['username']}#{user['discriminator']}")
            return token, user["id"]
        else:
            print(Fore.RED + "[!] Invalid token, please try again.")

def ask_mode():
    print(Fore.YELLOW + "\n[?] Choose mode:")
    print("[1] Delete messages in a specific channel")
    print("[2] Delete all your messages in all DMs and servers")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice in ('1', '2'):
            return choice
        else:
            print(Fore.RED + "[!] Invalid choice. Please enter 1 or 2.")

def ask_channel_id():
    while True:
        channel_id = input(Fore.YELLOW + "[?] Enter Channel ID: ").strip()
        if channel_id.isdigit():
            return channel_id
        print(Fore.RED + "[!] Invalid ID, must be numeric.")

def ask_message_limit():
    while True:
        choice = input(Fore.YELLOW + "[?] How many messages to delete? (or type 'all'): ").strip()
        if choice.lower() == "all" or choice.isdigit():
            return choice
        print(Fore.RED + "[!] Enter a number or 'all'.")

def ask_filter_keyword():
    use = input(Fore.YELLOW + "[Optional] Filter by keyword(s)? (y/n)(press Enter to skip): ").strip().lower()
    if use != 'y':
        return None
    keywords = input(Fore.YELLOW + "Enter keywords separated by | (example: hello|buy|test) (press Enter to skip): ").strip()
    if not keywords:
        return None
    return [k.strip().lower() for k in keywords.split('|') if k.strip()]

def ask_date_range():
    use = input(Fore.YELLOW + "[Optional] Filter by date range? (y/n)(press Enter to skip): ").strip().lower()
    if use != 'y':
        return None, None
    fmt = "%Y-%m-%d"
    while True:
        try:
            start = input(Fore.YELLOW + "[?] Start date (YYYY-MM-DD) (press Enter to skip): ").strip()
            end = input(Fore.YELLOW + "[?] End date (YYYY-MM-DD) (press Enter to skip): ").strip()
            if not start or not end:
                return None, None
            start_ts = int(datetime.strptime(start, fmt).timestamp() * 1000)
            end_ts = int(datetime.strptime(end, fmt).timestamp() * 1000)
            return start_ts, end_ts
        except:
            print(Fore.RED + "[!] Invalid format. Use YYYY-MM-DD.")

def ask_content_type_filter():
    print(Fore.YELLOW + "\n[Optional] Only delete messages with:")
    print("[1] No filter (default)")
    print("[2] Attachments only")
    print("[3] Links only")
    while True:
        opt = input("Select option 1-3: ").strip()
        if opt in ('1', '2', '3'):
            return opt
        print(Fore.RED + "[!] Invalid option.")

def fetch_messages(token, channel_id, limit=100, before=None):
    headers = {"Authorization": token}
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
    if before:
        url += f"&before={before}"
    while True:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(Fore.YELLOW + f"[!] Rate limited, waiting {retry}s...")
            time.sleep(retry)
        else:
            print(Fore.RED + f"[!] Failed fetching messages: {r.status_code}")
            return []

def delete_message(token, channel_id, message_id):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
    headers = {"Authorization": token}
    while True:
        r = requests.delete(url, headers=headers)
        if r.status_code == 204:
            return True
        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(Fore.YELLOW + f"[!] Rate limited while deleting, waiting {retry}s...")
            time.sleep(retry)
        else:
            print(Fore.RED + f"[!] Failed deleting message {message_id}: {r.status_code}")
            return False

def parse_timestamp(ts):
    try:
        return int(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z").timestamp() * 1000)
    except:
        return int(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").timestamp() * 1000)

def run_cleaner():
    token, my_id = ask_token()
    while True:
        clear()
        banner()
        mode = ask_mode()
        channels = []

        if mode == "1":
            channels = [ask_channel_id()]
        else:
            headers = {"Authorization": token}
            r = requests.get("https://discord.com/api/v9/users/@me/channels", headers=headers)
            if r.status_code == 200:
                data = r.json()
                channels = [c["id"] for c in data if c["type"] in (1, 3)]
                print(Fore.GREEN + f"[+] Found {len(channels)} DM/group channels.")
            else:
                print(Fore.RED + "[!] Failed to fetch DM channels.")
                return

        limit = ask_message_limit()
        keywords = ask_filter_keyword()
        start_ts, end_ts = ask_date_range()
        content_type = ask_content_type_filter()

        for cid in channels:
            count = 0
            before = None
            while True:
                fetch_limit = 100 if limit == "all" else min(100, int(limit) - count)
                if fetch_limit <= 0:
                    break
                messages = fetch_messages(token, cid, fetch_limit, before)
                if not messages:
                    break

                for msg in messages:
                    try:
                        if msg["author"]["id"] != my_id:
                            continue
                        content = msg.get("content", "").lower()
                        ts = parse_timestamp(msg["timestamp"])
                        if keywords and not any(k in content for k in keywords):
                            continue
                        if start_ts and end_ts and not (start_ts <= ts <= end_ts):
                            continue
                        if content_type == "2" and not msg["attachments"]:
                            continue
                        if content_type == "3" and "http" not in content:
                            continue
                        success = delete_message(token, cid, msg["id"])
                        if success:
                            print(Fore.GREEN + f"[+] Deleted: {msg['id']}")
                            time.sleep(2)  # Increased delay to avoid rate limit
                        if limit != "all":
                            count += 1
                            if count >= int(limit):
                                break
                    except Exception as e:
                        print(Fore.RED + f"[!] Error processing message: {e}")

                if len(messages) < 100 or (limit != "all" and count >= int(limit)):
                    break
                before = messages[-1]["id"]

            print(Fore.CYAN + f"\n[✓] Finished channel: {cid} | Total deleted: {count}")

        again = input(Fore.YELLOW + "\n[?] Delete messages in another channel? (y/n): ").strip().lower()
        if again != 'y':
            print(Fore.GREEN + "Goodbye!")
            break

def main():
    clear()
    banner()
    run_cleaner()

if __name__ == "__main__":
    main()
