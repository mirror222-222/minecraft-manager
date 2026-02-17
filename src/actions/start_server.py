import subprocess
import os
import datetime
import time
import json

def log_error(message, exc=None):
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry)

def start_server():
    try:
        apt = subprocess.run(["apt", "update"], capture_output=True, text=True)
        if apt.returncode != 0:
            msg = f"apt update failed: {apt.stderr}"
            log_error(msg)
            return False, msg
        server_jar = "server.jar"
        if not os.path.exists(server_jar):
            # Fetch the latest Minecraft server JAR URL
            import urllib.request
            try:
                version_manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
                with urllib.request.urlopen(version_manifest_url) as response:
                    manifest = response.read().decode()
                manifest_json = json.loads(manifest)
                latest_release = manifest_json["latest"]["release"]
                version_info = next(v for v in manifest_json["versions"] if v["id"] == latest_release)
                version_url = version_info["url"]
                with urllib.request.urlopen(version_url) as response:
                    version_data = response.read().decode()
                version_json = json.loads(version_data)
                url = version_json["downloads"]["server"]["url"]
            except Exception as e:
                msg = f"Failed to fetch latest server JAR URL: {e}"
                log_error(msg)
                return False, msg
            dl = subprocess.run(["wget", "-O", server_jar, url], capture_output=True, text=True)
            if dl.returncode != 0:
                msg = f"Download failed: {dl.stderr}"
                log_error(msg)
                return False, msg
        with open("eula.txt", "w") as f:
            f.write("eula=true\n")
        props = "server.properties"
        if os.path.exists(props):
            with open(props) as f:
                lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if line.startswith("enforce-whitelist"):
                    lines[i] = "enforce-whitelist=true\n"
                    found = True
            if not found:
                lines.append("enforce-whitelist=true\n")
            with open(props, "w") as f:
                f.writelines(lines)
        else:
            with open(props, "w") as f:
                f.write("enforce-whitelist=true\n")
        start = subprocess.run(["systemctl", "start", "minecraft"], capture_output=True, text=True)
        if start.returncode != 0:
            msg = f"Failed to start server: {start.stderr}"
            log_error(msg)
            return False, msg
        return True, "Server started"
    except Exception as e:
        log_error("start_server exception", e)
        return False, str(e)

if __name__ == "__main__":
    success, msg = start_server()
    print(json.dumps({"success": success, "message": msg}))
