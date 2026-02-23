#!/usr/bin/env python3
import argparse
import json
import platform
import socket
import subprocess
from pathlib import Path

DEFAULT_PORTS = [3000, 6000, 8883, 990]


def ping(ip: str):
    p = subprocess.run(["ping", "-c", "2", "-W", "1", ip], capture_output=True, text=True)
    ok = p.returncode == 0
    return {"ok": ok, "raw": (p.stdout or p.stderr).strip()}


def check_port(ip: str, port: int, timeout=0.8):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def bambu_studio_info():
    exe = Path('/mnt/c/Program Files/Bambu Studio/bambu-studio.exe')
    out = {
        "installed": exe.exists(),
        "path": str(exe) if exe.exists() else None,
        "cli_help_ok": False,
        "version_header": None,
    }
    if not exe.exists():
        return out
    p = subprocess.run([str(exe), "--help"], capture_output=True, text=True)
    text = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    out["cli_help_ok"] = "Usage: bambu-studio" in text
    for line in text.splitlines():
        if line.startswith("BambuStudio-"):
            out["version_header"] = line.strip()
            break
    return out


def main():
    ap = argparse.ArgumentParser(description="Read-only Bambu LAN probe")
    ap.add_argument("--ip", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ports = {p: check_port(args.ip, p) for p in DEFAULT_PORTS}
    studio = bambu_studio_info()

    report = {
        "target_ip": args.ip,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "ping": ping(args.ip),
        "ports": ports,
        "bambu_studio": studio,
        "ready": bool(studio.get("installed") and studio.get("cli_help_ok") and ports.get(8883) and ports.get(990)),
        "note": "Read-only checks only; no printer state changes made."
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Bambu Probe: {args.ip}")
        print(f"- ping: {'ok' if report['ping']['ok'] else 'fail'}")
        for p,v in ports.items():
            print(f"- port {p}: {'open' if v else 'closed'}")
        print(f"- studio installed: {studio['installed']}")
        print(f"- studio cli help: {studio['cli_help_ok']}")
        print(f"- ready: {report['ready']}")


if __name__ == '__main__':
    main()
