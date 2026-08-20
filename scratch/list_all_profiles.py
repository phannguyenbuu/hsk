# scratch/list_all_profiles.py
import os
import datetime

user_data_path = os.path.join(
    os.environ['USERPROFILE'],
    r'AppData\Local\Google\Chrome\User Data'
)

print(f"User Data Path: {user_data_path}")
if not os.path.exists(user_data_path):
    print("Chrome User Data directory does not exist.")
    exit(1)

# List all folders in User Data
dirs = [d for d in os.listdir(user_data_path) if os.path.isdir(os.path.join(user_data_path, d))]

profile_dirs = []
for d in dirs:
    if d == "Default" or d.startswith("Profile "):
        profile_dirs.append(d)

print(f"Found {len(profile_dirs)} profile directories:")
for p in sorted(profile_dirs):
    p_path = os.path.join(user_data_path, p)
    cookies_path = os.path.join(p_path, "Network", "Cookies")
    
    if os.path.exists(cookies_path):
        mtime = os.path.getmtime(cookies_path)
        dt = datetime.datetime.fromtimestamp(mtime)
        size = os.path.getsize(cookies_path)
        print(f"- {p}: size={size} bytes, last modified={dt}")
    else:
        # Check top-level Cookies (older Chrome versions)
        cookies_top = os.path.join(p_path, "Cookies")
        if os.path.exists(cookies_top):
            mtime = os.path.getmtime(cookies_top)
            dt = datetime.datetime.fromtimestamp(mtime)
            size = os.path.getsize(cookies_top)
            print(f"- {p}: size={size} bytes (top-level), last modified={dt}")
        else:
            print(f"- {p}: No Cookies database found")
