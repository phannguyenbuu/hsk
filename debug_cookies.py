import os
import shutil
import subprocess
import time
import urllib.request
import json
import websocket

def debug_cookies():
    original_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    original_profile = "Profile 15"
    
    temp_user_data = os.path.abspath("temp_chrome_user_data")
    temp_profile_dir = os.path.join(temp_user_data, "Default")
    temp_network_dir = os.path.join(temp_profile_dir, "Network")
    
    if os.path.exists(temp_user_data):
        shutil.rmtree(temp_user_data)
        
    os.makedirs(temp_network_dir, exist_ok=True)
    
    shutil.copy2(
        os.path.join(original_user_data_dir, "Local State"),
        os.path.join(temp_user_data, "Local State")
    )
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Preferences"),
        os.path.join(temp_profile_dir, "Preferences")
    )
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Secure Preferences"),
        os.path.join(temp_profile_dir, "Secure Preferences")
    )
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Network", "Cookies"),
        os.path.join(temp_network_dir, "Cookies")
    )
    
    cookies_before_size = os.path.getsize(os.path.join(temp_network_dir, "Cookies"))
    print(f"Cookies file size before Chrome start: {cookies_before_size} bytes")
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_user_data}",
        "--profile-directory=Default",
        "--no-first-run",
        "--headless",
        "--remote-allow-origins=*"
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    cookies_after_size = os.path.getsize(os.path.join(temp_network_dir, "Cookies"))
    print(f"Cookies file size after Chrome start: {cookies_after_size} bytes")
    
    try:
        url = "http://localhost:9222/json/version"
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        ws_url = data['webSocketDebuggerUrl']
        
        ws = websocket.create_connection(ws_url)
        
        # Method 1: Network.getAllCookies
        msg = {"id": 1, "method": "Network.getAllCookies"}
        ws.send(json.dumps(msg))
        res = json.loads(ws.recv())
        print("Network.getAllCookies response keys:", res.keys())
        if 'error' in res:
            print("  Error:", res['error'])
        else:
            cookies = res.get('result', {}).get('cookies', [])
            print(f"  Got {len(cookies)} cookies.")
            
        # Method 2: Storage.getCookies
        msg2 = {"id": 2, "method": "Storage.getCookies"}
        ws.send(json.dumps(msg2))
        res2 = json.loads(ws.recv())
        print("Storage.getCookies response keys:", res2.keys())
        if 'error' in res2:
            print("  Error:", res2['error'])
        else:
            cookies2 = res2.get('result', {}).get('cookies', [])
            print(f"  Got {len(cookies2)} cookies.")
            
        # Check target list
        url_targets = "http://localhost:9222/json"
        req_t = urllib.request.urlopen(url_targets)
        targets = json.loads(req_t.read().decode())
        print(f"Active targets: {len(targets)}")
        for t in targets:
            print(f"  Target: {t.get('type')} - {t.get('url')}")
            
        ws.close()
    except Exception as e:
        print("CDP Error:", e)
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    debug_cookies()
