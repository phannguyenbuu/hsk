import subprocess
import time
import urllib.request
import json
import os
import shutil
import websocket

def get_cookies_page():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    original_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    profile = "Profile 15"
    
    # Define temp user data directory in workspace
    temp_user_data = os.path.abspath("temp_chrome_user_data")
    temp_profile_dir = os.path.join(temp_user_data, profile)
    temp_network_dir = os.path.join(temp_profile_dir, "Network")
    
    # Clean up previous temp dir if exists
    # If locked, we can try to clean it first
    if os.path.exists(temp_user_data):
        try:
            shutil.rmtree(temp_user_data)
        except Exception as e:
            print(f"Warning: Could not clean old temp dir: {e}")
            
    # Create directories
    os.makedirs(temp_network_dir, exist_ok=True)
    
    # Copy Local State
    shutil.copy2(
        os.path.join(original_user_data_dir, "Local State"),
        os.path.join(temp_user_data, "Local State")
    )
    
    # Copy Cookies
    shutil.copy2(
        os.path.join(original_user_data_dir, profile, "Network", "Cookies"),
        os.path.join(temp_network_dir, "Cookies")
    )
    
    print("Files successfully copied. Starting Chrome...")

    # Start Chrome with remote debugging enabled using temp user-data-dir
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_user_data}",
        f"--profile-directory={profile}",
        "--headless=new",
        "--remote-allow-origins=http://127.0.0.1:9222"
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
        return
        
    try:
        # Create a new tab targeting https://hskstory.com
        print("Opening tab for https://hskstory.com...")
        new_tab_url = "http://127.0.0.1:9222/json/new?https://hskstory.com"
        req = urllib.request.Request(new_tab_url, method='PUT')
        res = urllib.request.urlopen(req)
        tab_data = json.loads(res.read().decode())
        
        ws_url = tab_data['webSocketDebuggerUrl']
        ws_url = ws_url.replace("localhost", "127.0.0.1")
        print(f"Connected to Tab WebSocket: {ws_url}")
        
        # Connect to page websocket
        ws = websocket.create_connection(ws_url, timeout=5)
        
        # Enable Network domain
        ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        ws.recv() # Wait for response
        
        # Request cookies for the current tab
        msg = {
            "id": 2,
            "method": "Network.getCookies",
            "params": {
                "urls": ["https://hskstory.com"]
            }
        }
        ws.send(json.dumps(msg))
        
        # Read response
        result = ws.recv()
        res_data = json.loads(result)
        
        ws.close()
        
        cookies = res_data.get('result', {}).get('cookies', [])
        print(f"\nRetrieved {len(cookies)} cookies for hskstory.com.")
        
        for c in cookies:
            print(f"Domain: {c.get('domain')}")
            print(f"  Name:  {c.get('name')}")
            print(f"  Value: {c.get('value')}")
            print(f"  Path:  {c.get('path')}")
            print("-" * 40)
            
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
        
        # Clean up temp files
        try:
            shutil.rmtree(temp_user_data)
            os.remove("chrome_stdout.log")
            os.remove("chrome_stderr.log")
            print("Temp files cleaned up.")
        except Exception as e:
            print(f"Warning: Could not remove temporary files: {e}")

if __name__ == '__main__':
    get_cookies_page()
