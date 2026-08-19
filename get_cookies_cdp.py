import subprocess
import time
import urllib.request
import json
import os
import shutil
import websocket

def get_cookies_cdp():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    original_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    original_profile = "Profile 15"
    
    # Define temp user data directory in workspace
    temp_user_data = os.path.abspath("temp_chrome_user_data")
    temp_profile_dir = os.path.join(temp_user_data, "Default")
    temp_network_dir = os.path.join(temp_profile_dir, "Network")
    
    # Clean up previous temp dir if exists
    if os.path.exists(temp_user_data):
        try:
            shutil.rmtree(temp_user_data)
        except Exception as e:
            print(f"Warning: Could not clean old temp dir: {e}")
            
    # Create directories
    os.makedirs(temp_network_dir, exist_ok=True)
    
    # Files to copy
    # 1. Local State (root)
    shutil.copy2(
        os.path.join(original_user_data_dir, "Local State"),
        os.path.join(temp_user_data, "Local State")
    )
    
    # 2. Preferences (Default profile folder)
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Preferences"),
        os.path.join(temp_profile_dir, "Preferences")
    )
    
    # 3. Secure Preferences (Default profile folder)
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Secure Preferences"),
        os.path.join(temp_profile_dir, "Secure Preferences")
    )
    
    # 4. Cookies (Network folder)
    shutil.copy2(
        os.path.join(original_user_data_dir, original_profile, "Network", "Cookies"),
        os.path.join(temp_network_dir, "Cookies")
    )
    
    print("Files successfully copied. Starting Chrome...")

    # Start Chrome with remote debugging enabled using temp user-data-dir
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_user_data}",
        "--headless",
        "--remote-allow-origins=*"
    ]
    
    stdout_file = open("chrome_stdout.log", "w", encoding="utf-8")
    stderr_file = open("chrome_stderr.log", "w", encoding="utf-8")
    
    proc = subprocess.Popen(cmd, stdout=stdout_file, stderr=stderr_file)
    
    # Wait for Chrome to initialize
    time.sleep(5)
    
    # Check if process is still running
    poll = proc.poll()
    if poll is not None:
        print(f"Chrome exited immediately with code {poll}")
        stdout_file.close()
        stderr_file.close()
        with open("chrome_stderr.log", "r", encoding="utf-8") as f:
            print("Chrome Stderr:")
            print(f.read())
        return
        
    try:
        # Get websocket URL
        url = "http://localhost:9222/json/version"
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        ws_url = data['webSocketDebuggerUrl']
        print(f"Connected to Chrome debugging. WebSocket URL: {ws_url}")
        
        # Connect to websocket
        ws = websocket.create_connection(ws_url)
        
        # Request cookies
        msg = {
            "id": 1,
            "method": "Network.getAllCookies"
        }
        ws.send(json.dumps(msg))
        
        # Read response
        result = ws.recv()
        res_data = json.loads(result)
        
        ws.close()
        
        cookies = res_data.get('result', {}).get('cookies', [])
        print(f"\nRetrieved {len(cookies)} cookies in total.")
        
        found = False
        for c in cookies:
            if 'hskstory.com' in c.get('domain', ''):
                print(f"Domain: {c.get('domain')}")
                print(f"  Name:  {c.get('name')}")
                print(f"  Value: {c.get('value')}")
                print(f"  Path:  {c.get('path')}")
                print("-" * 40)
                found = True
        
        if not found:
            print("No cookies for hskstory.com found in this profile.")
            
    except Exception as e:
        print(f"Error during CDP communication: {e}")
    finally:
        print("Stopping Chrome...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        
        stdout_file.close()
        stderr_file.close()
        
        # try:
        #     shutil.rmtree(temp_user_data)
        #     os.remove("chrome_stdout.log")
        #     os.remove("chrome_stderr.log")
        #     print("Temp files cleaned up.")
        # except Exception as e:
        #     print(f"Warning: Could not remove temporary files: {e}")
        pass

if __name__ == '__main__':
    get_cookies_cdp()
