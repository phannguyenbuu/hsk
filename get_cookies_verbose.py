import os
import shutil
import subprocess
import time
import urllib.request
import json
import websocket

def run_verbose():
    original_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    original_profile = "Profile 15"
    
    temp_user_data = os.path.abspath("temp_chrome_user_data")
    temp_profile_dir = os.path.join(temp_user_data, "Default")
    temp_network_dir = os.path.join(temp_profile_dir, "Network")
    
    if os.path.exists(temp_user_data):
        try:
            shutil.rmtree(temp_user_data)
        except Exception as e:
            print(f"Warning: Could not remove old temp dir: {e}")
            
    os.makedirs(temp_network_dir, exist_ok=True)
    
    shutil.copy2(
        os.path.join(original_user_data_dir, "Local State"),
        os.path.join(temp_user_data, "Local State")
    )
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Network", "Cookies"),
        os.path.join(temp_network_dir, "Cookies")
    )
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_user_data}",
        "--profile-directory=Default",
        "--no-first-run",
        "--headless",
        "--remote-allow-origins=*",
        "--enable-logging",
        "--v=1"
    ]
    
    print("Starting Chrome with verbose logging...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    ws_connected = False
    try:
        url = "http://localhost:9222/json/version"
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        ws_url = data['webSocketDebuggerUrl']
        
        ws = websocket.create_connection(ws_url, timeout=5)
        ws_connected = True
        
        msg = {"id": 1, "method": "Storage.getCookies"}
        ws.send(json.dumps(msg))
        res = json.loads(ws.recv())
        
        cookies = res.get('result', {}).get('cookies', [])
        print(f"CDP Result: Got {len(cookies)} cookies.")
        
        for c in cookies:
            if 'hskstory.com' in c.get('domain', ''):
                print(f"Found cookie: {c.get('name')} = {c.get('value')}")
                
        ws.close()
    except Exception as e:
        print("CDP Error during run:", e)
    finally:
        print("Stopping Chrome...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            
    # Read chrome_debug.log
    debug_log_path = os.path.join(temp_user_data, "chrome_debug.log")
    if os.path.exists(debug_log_path):
        print("\n=== chrome_debug.log contents ===")
        with open(debug_log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            # Print last 50 lines to see if there are interesting cookie/decryption logs
            for line in lines[-50:]:
                print(line.strip())
    else:
        print("\nNo chrome_debug.log found.")

if __name__ == '__main__':
    run_verbose()
