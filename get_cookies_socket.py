import subprocess
import time
import urllib.request
import json
import os
import shutil
import socket
import re

def send_ws_frame(sock, text):
    payload = text.encode('utf-8')
    length = len(payload)
    
    frame = bytearray()
    frame.append(0x81) # FIN=1, Opcode=1 (Text)
    
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(length.to_bytes(2, byteorder='big'))
    else:
        frame.append(0x80 | 127)
        frame.extend(length.to_bytes(8, byteorder='big'))
        
    # Masking key: 4 bytes of 0x00 (makes XOR a no-op)
    frame.extend([0, 0, 0, 0])
    frame.extend(payload)
    sock.sendall(frame)

def recv_ws_frame(sock):
    header = sock.recv(2)
    if not header:
        return None
    fin_opcode = header[0]
    mask_len = header[1]
    
    masked = (mask_len & 0x80) != 0
    length = mask_len & 0x7f
    
    if length == 126:
        length_bytes = sock.recv(2)
        length = int.from_bytes(length_bytes, byteorder='big')
    elif length == 127:
        length_bytes = sock.recv(8)
        length = int.from_bytes(length_bytes, byteorder='big')
        
    mask_key = b""
    if masked:
        mask_key = sock.recv(4)
        
    payload = bytearray()
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            break
        payload.extend(chunk)
        
    if masked:
        unmasked = bytearray(len(payload))
        for i in range(len(payload)):
            unmasked[i] = payload[i] ^ mask_key[i % 4]
        return unmasked.decode('utf-8', errors='ignore')
    else:
        return payload.decode('utf-8', errors='ignore')

def get_cookies_socket():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    original_user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    profile = "Profile 15"
    
    # Define temp user data directory in workspace
    temp_user_data = os.path.abspath("temp_chrome_user_data")
    temp_profile_dir = os.path.join(temp_user_data, profile)
    temp_network_dir = os.path.join(temp_profile_dir, "Network")
    
    # Clean up previous temp dir if exists
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
        
    s = None
    try:
        # Create a new tab targeting https://hskstory.com
        print("Opening tab for https://hskstory.com...")
        new_tab_url = "http://127.0.0.1:9222/json/new?https://hskstory.com"
        req = urllib.request.Request(new_tab_url, method='PUT')
        res = urllib.request.urlopen(req)
        tab_data = json.loads(res.read().decode())
        
        ws_url = tab_data['webSocketDebuggerUrl']
        print(f"Connected tab info. ws_url: {ws_url}")
        
        # Parse host, port, and path from ws_url
        # Format: ws://127.0.0.1:9222/devtools/page/...
        match = re.match(r"ws://([^:/]+):(\d+)(/.+)", ws_url)
        if not match:
            print("Failed to parse websocket URL")
            return
            
        host, port, path = match.groups()
        port = int(port)
        
        # Connect raw socket
        print(f"Connecting raw socket to {host}:{port}...")
        s = socket.create_connection((host, port), timeout=5)
        
        # Perform WebSocket handshake
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Origin: http://127.0.0.1:9222\r\n\r\n"
        )
        s.sendall(handshake.encode())
        
        # Read handshake response
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk
            
        print("Handshake Response:")
        headers_part = response.split(b"\r\n\r\n")[0].decode('utf-8', errors='ignore')
        print(headers_part)
        
        if "101" not in headers_part:
            print("Failed WebSocket handshake!")
            return
            
        print("WebSocket handshake successful!")
        
        # Enable Network domain
        print("Enabling Network domain...")
        send_ws_frame(s, json.dumps({"id": 1, "method": "Network.enable"}))
        recv_ws_frame(s) # Read response
        
        # Wait 5 seconds for the page to load and cookies to be decrypted in the background
        print("Waiting 5 seconds for page load and cookie decryption...")
        time.sleep(5)
        
        # Request cookies for the current tab
        print("Requesting cookies...")
        msg = {
            "id": 2,
            "method": "Network.getCookies",
            "params": {
                "urls": ["https://hskstory.com"]
            }
        }
        send_ws_frame(s, json.dumps(msg))
        
        # Read cookies response
        result = recv_ws_frame(s)
        print("CDP Raw Response:", result)
        res_data = json.loads(result)
        
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
        if s:
            s.close()
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
    get_cookies_socket()
