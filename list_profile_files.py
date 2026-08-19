import os

user_data_path = os.path.join(
    os.environ['USERPROFILE'],
    r'AppData\Local\Google\Chrome\User Data'
)
profile_15_path = os.path.join(user_data_path, "Profile 15")

if os.path.exists(profile_15_path):
    print("Files in Profile 15:")
    for root, dirs, files in os.walk(profile_15_path):
        # Only show top-level files and Network folder files to avoid spam
        rel_path = os.path.relpath(root, profile_15_path)
        if rel_path == "." or rel_path.startswith("Network"):
            for f in files:
                p = os.path.join(root, f)
                print(f"  {os.path.join(rel_path, f)}: {os.path.getsize(p)} bytes")
else:
    print("Profile 15 does not exist.")
