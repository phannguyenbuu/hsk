import os
import json
import base64
import sqlite3
import shutil
import tempfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import win32crypt

def get_encryption_key():
    local_state_path = os.path.join(
        os.environ['USERPROFILE'],
        r'AppData\Local\Google\Chrome\User Data\Local State'
    )
    if not os.path.exists(local_state_path):
        print(f"Error: Local State file not found at {local_state_path}")
        return None
        
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        # DPAPI prefix is 5 bytes 'DPAPI'
        encrypted_key = encrypted_key[5:]
        decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return decrypted_key
    except Exception as e:
        print(f"Error retrieving key: {e}")
        return None

def decrypt_cookie(value, key):
    try:
        prefix = value[:3]
        if prefix in (b'v10', b'v11'):
            iv = value[3:15]
            ciphertext = value[15:]
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(iv, ciphertext, None)
            return decrypted.decode('utf-8', errors='ignore')
        else:
            decrypted = win32crypt.CryptUnprotectData(value, None, None, None, 0)[1]
            return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"[Decryption Error: {e}, len={len(value)}, prefix={value[:10]}]"

def find_cookie_databases():
    user_data_path = os.path.join(
        os.environ['USERPROFILE'],
        r'AppData\Local\Google\Chrome\User Data'
    )
    paths = []
    if not os.path.exists(user_data_path):
        return paths
        
    for root, dirs, files in os.walk(user_data_path):
        for file in files:
            if file == 'Cookies':
                full_path = os.path.join(root, file)
                parts = full_path.split(os.sep)
                try:
                    ud_idx = parts.index('User Data')
                    if len(parts) > ud_idx + 1:
                        paths.append((parts[ud_idx + 1], full_path))
                except ValueError:
                    pass
    return paths

def copy_locked_file(src, dst):
    # Try a simple byte-by-byte read, which might succeed under certain sharing locks
    try:
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                # Read in chunks
                while True:
                    buf = fsrc.read(1024 * 1024)
                    if not buf:
                        break
                    fdst.write(buf)
        return True
    except Exception as e:
        print(f"  Simple read copy failed: {e}")
        return False

def get_cookies_for_domain(domain_pattern):
    key = get_encryption_key()
    if not key:
        return
        
    cookie_dbs = find_cookie_databases()
    if not cookie_dbs:
        print("No Cookies databases found.")
        return
        
    print(f"Searching for cookies containing domain: '{domain_pattern}'")
    
    found_any = False
    for profile, db_path in cookie_dbs:
        print(f"\nScanning profile: {profile} ({db_path})")
        
        # Try copying the file first
        temp_dir = tempfile.gettempdir()
        temp_db = os.path.join(temp_dir, f"chrome_cookies_{profile}.db")
        
        copied = False
        # Method 1: shutil.copy2
        try:
            shutil.copy2(db_path, temp_db)
            copied = True
        except Exception as e:
            # Method 2: Simple binary read/write copy
            copied = copy_locked_file(db_path, temp_db)
            
        if not copied:
            # Method 3: Try to connect directly using sqlite URI read-only query mode
            print("  Warning: Database copy failed. Trying direct read-only connection...")
            try:
                # file:path?mode=ro
                uri_path = f"file:{db_path.replace(os.sep, '/')}?mode=ro"
                conn = sqlite3.connect(uri_path, uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                # If we succeeded, we'll use db_path directly
                temp_db = db_path
                copied = True
                print("  Direct read-only connection succeeded!")
            except Exception as direct_e:
                print(f"  Direct connection failed: {direct_e}")
                continue
            
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            query = """
            SELECT host_key, name, value, encrypted_value, path 
            FROM cookies 
            WHERE host_key LIKE ?
            """
            cursor.execute(query, (f"%{domain_pattern}%",))
            
            rows = cursor.fetchall()
            if not rows:
                print("  No matching cookies in this profile.")
                conn.close()
                continue
                
            found_any = True
            for host_key, name, value, encrypted_value, path in rows:
                decrypted_val = ""
                if encrypted_value:
                    decrypted_val = decrypt_cookie(encrypted_value, key)
                else:
                    decrypted_val = value
                    
                print(f"  Domain: {host_key}")
                print(f"    Name:  {name}")
                print(f"    Value: {decrypted_val}")
                print(f"    Path:  {path}")
                print("-" * 40)
                
            conn.close()
        except Exception as e:
            print(f"  Error reading database: {e}")
        finally:
            if temp_db != db_path and os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass

    if not found_any:
        print(f"\nNo cookies matching '{domain_pattern}' were found in any Chrome profile.")

if __name__ == '__main__':
    get_cookies_for_domain('hskstory.com')
