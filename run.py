#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if zs.py exists
    if not os.path.exists("zs.py"):
        print("[!] zslk.py not found!")
        print("[*] Please make sure zs.py is in the same directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("[!] Python 3.7 or higher is required")
        sys.exit(1)
    
    # Install required packages if not installed
    required_packages = [
        "requests",
        "aiohttp",
        "pycryptodome"
    ]
    
    print("[*] Checking required packages...")
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"[*] Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Run zs.py
    print("[*] Starting RUIJIE Voucher Bypass System...")
    os.system(f"{sys.executable} zs.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)
