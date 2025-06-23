import json
import os
import secrets
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv, set_key

load_dotenv()

KEY_FILE = ".env"
KEY_ENV = "ACCOUNT_AES_KEY"
ACCOUNT_FILE = "account.enc"
COOKIE_FILE = "cookie.enc"
BLOCK_SIZE = 16

def reset_env():
    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)
    print(".env文件已重置。下次运行将自动生成新密钥。")

def get_key():
    load_dotenv()
    key = os.getenv(KEY_ENV)
    if not key or len(key) not in (16, 24, 32):
        # 自动生成32字节高强度密钥
        key = secrets.token_urlsafe(48)[:32]
        set_key(KEY_FILE, KEY_ENV, key)
        print(f"已自动生成32字节AES密钥并写入{KEY_FILE}，请妥善备份：{key}")
    return key.encode("utf-8")

def pad(s):
    pad_len = BLOCK_SIZE - len(s) % BLOCK_SIZE
    return s + chr(pad_len) * pad_len

def unpad(s):
    pad_len = ord(s[-1])
    return s[:-pad_len]

def save_account(platform, account_dict):
    key = get_key()
    accounts = {}
    if os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, "rb") as f:
            raw = f.read()
            if raw:
                iv = raw[:BLOCK_SIZE]
                cipher = AES.new(key, AES.MODE_CBC, iv)
                data = unpad(cipher.decrypt(raw[BLOCK_SIZE:]).decode("utf-8"))
                accounts = json.loads(data)
    accounts[platform] = account_dict
    data = json.dumps(accounts)
    iv = get_random_bytes(BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc = iv + cipher.encrypt(pad(data).encode("utf-8"))
    with open(ACCOUNT_FILE, "wb") as f:
        f.write(enc)

def load_account(platform):
    key = get_key()
    if not os.path.exists(ACCOUNT_FILE):
        return None
    with open(ACCOUNT_FILE, "rb") as f:
        raw = f.read()
        if not raw:
            return None
        iv = raw[:BLOCK_SIZE]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = unpad(cipher.decrypt(raw[BLOCK_SIZE:]).decode("utf-8"))
        accounts = json.loads(data)
        return accounts.get(platform)

def save_cookie(platform, cookie_dict):
    key = get_key()
    cookies = {}
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "rb") as f:
            raw = f.read()
            if raw:
                iv = raw[:BLOCK_SIZE]
                cipher = AES.new(key, AES.MODE_CBC, iv)
                data = unpad(cipher.decrypt(raw[BLOCK_SIZE:]).decode("utf-8"))
                cookies = json.loads(data)
    cookies[platform] = cookie_dict
    data = json.dumps(cookies)
    iv = get_random_bytes(BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc = iv + cipher.encrypt(pad(data).encode("utf-8"))
    with open(COOKIE_FILE, "wb") as f:
        f.write(enc)

def load_cookie(platform):
    key = get_key()
    if not os.path.exists(COOKIE_FILE):
        return None
    with open(COOKIE_FILE, "rb") as f:
        raw = f.read()
        if not raw:
            return None
        iv = raw[:BLOCK_SIZE]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = unpad(cipher.decrypt(raw[BLOCK_SIZE:]).decode("utf-8"))
        cookies = json.loads(data)
        return cookies.get(platform) 