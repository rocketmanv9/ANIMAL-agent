#!/usr/bin/env python3
import argparse
import json
import socket
import subprocess
import urllib.request

COMMON_PORTS = [554, 8554, 6000, 3000, 80, 443]
COMMON_PATHS = [
    "/",
    "/live",
    "/video",
    "/stream",
    "/snapshot",
]


def ping(ip: str):
    p = subprocess.run(["ping", "-c", "2", "-W", "1", ip], capture_output=True, text=True)
    return {"ok": p.returncode == 0, "output": (p.stdout or p.stderr).strip()}


def port_open(ip: str, port: int, timeout=0.8):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def probe_http(ip: str, port: int, path: str):
    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{ip}:{port}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ANIMAL-camera-probe/1.0"})
        with urllib.request.urlopen(req, timeout=2) as r:
            ct = r.headers.get("Content-Type", "")
            return {"url": url, "ok": True, "status": r.status, "contentType": ct}
    except Exception as e:
        return {"url": url, "ok": False, "error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="Read-only Bambu camera/network probe")
    ap.add_argument("--ip", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = ping(args.ip)
    ports = {port: port_open(args.ip, port) for port in COMMON_PORTS}

    http_results = []
    for port in [80, 443, 3000, 6000]:
        if ports.get(port):
            for path in COMMON_PATHS:
                http_results.append(probe_http(args.ip, port, path))

    rtsp_candidates = [
        f"rtsp://{args.ip}:554/live",
        f"rtsp://{args.ip}:8554/live",
        f"rtsp://{args.ip}:6000/live",
        f"rtsp://bblp:<ACCESS_CODE>@{args.ip}:322/streaming/live/1",
    ]

    out = {
        "target": args.ip,
        "ping": p,
        "ports": ports,
        "httpProbe": http_results,
        "rtspCandidates": rtsp_candidates,
        "cameraLikelyReachable": any(ports.get(x) for x in [554, 8554, 6000]),
        "note": "Read-only probe only. No printer state changes."
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Bambu Camera Probe: {args.ip}")
        print(f"- ping: {'ok' if p['ok'] else 'fail'}")
        for k, v in ports.items():
            print(f"- port {k}: {'open' if v else 'closed'}")
        print(f"- cameraLikelyReachable: {out['cameraLikelyReachable']}")
        if http_results:
            print("- httpProbe hits:")
            for r in http_results[:8]:
                print(f"  - {r['url']} => {'ok' if r['ok'] else 'fail'}")
        print("- rtspCandidates:")
        for c in rtsp_candidates:
            print(f"  - {c}")


if __name__ == "__main__":
    main()
