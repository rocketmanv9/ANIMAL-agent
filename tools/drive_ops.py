#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

GOG = os.environ.get("GOG_BIN", "/mnt/c/Users/grant/bin/gogcli/gog.exe")
ACCOUNT = os.environ.get("GOG_ACCOUNT", "grant.m.anderson2021@gmail.com")
CACHE_PATH = Path(os.environ.get("DRIVE_OPS_CACHE", "/home/grant/.openclaw/workspace/.openclaw/drive_id_cache.json"))
CACHE_TTL = int(os.environ.get("DRIVE_OPS_CACHE_TTL", "900"))  # 15m


def run_gog(args, plain=True, check=True):
    cmd = [GOG, "-a", ACCOUNT]
    if plain:
        cmd.append("--plain")
    cmd.extend(args)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p


def parse_kv_plain(out: str):
    d = {}
    for line in out.splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            d[k.strip()] = v.strip()
    return d


def parse_table_plain(out: str):
    lines = [l for l in out.splitlines() if l.strip()]
    if len(lines) <= 1:
        return []
    headers = lines[0].split("\t")
    rows = []
    for l in lines[1:]:
        parts = l.split("\t")
        row = {headers[i]: (parts[i] if i < len(parts) else "") for i in range(len(headers))}
        rows.append(row)
    return rows


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def cache_get(key):
    c = load_cache()
    item = c.get(key)
    if not item:
        return None
    if time.time() - item.get("ts", 0) > CACHE_TTL:
        return None
    return item.get("value")


def cache_set(key, value):
    c = load_cache()
    c[key] = {"value": value, "ts": time.time()}
    save_cache(c)


def find_folder_id(name, parent="root", refresh=False):
    key = f"folder:{parent}:{name}"
    if not refresh:
        v = cache_get(key)
        if v:
            return v
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name.replace("'", "\\'")}' and '{parent}' in parents and trashed=false"
    p = run_gog(["drive", "ls", "--query", q, "--max", "50"])
    rows = parse_table_plain(p.stdout)
    if not rows:
        return None
    fid = rows[0].get("ID")
    if fid:
        cache_set(key, fid)
    return fid


def cmd_mkdir(args):
    existing = find_folder_id(args.name, args.parent)
    if existing:
        print(json.dumps({"ok": True, "id": existing, "name": args.name, "created": False}))
        return
    p = run_gog(["drive", "mkdir", args.name, "--parent", args.parent])
    d = parse_kv_plain(p.stdout)
    fid = d.get("id")
    if fid:
        cache_set(f"folder:{args.parent}:{args.name}", fid)
    print(json.dumps({"ok": True, "id": fid, "name": d.get("name", args.name), "created": True, "link": d.get("link")}))


def cmd_ls(args):
    p = run_gog(["drive", "ls", "--parent", args.parent, "--max", str(args.max)])
    rows = parse_table_plain(p.stdout)
    print(json.dumps({"ok": True, "count": len(rows), "items": rows}, indent=2))


def cmd_doc(args):
    parent = args.parent
    if args.parent_name:
        parent = find_folder_id(args.parent_name, args.parent_base)
        if not parent:
            raise RuntimeError(f"parent folder not found: {args.parent_name}")
    p = run_gog(["docs", "create", args.title, "--parent", parent])
    d = parse_kv_plain(p.stdout)
    doc_id = d.get("id")
    if args.content:
        run_gog(["docs", "write", doc_id, args.content, "--replace"])
    elif args.file:
        cmd = ["docs", "write", doc_id, "--file", args.file, "--replace"]
        if args.markdown:
            cmd.append("--markdown")
        run_gog(cmd)
    print(json.dumps({"ok": True, "id": doc_id, "name": d.get("name", args.title), "link": d.get("link")}))


def cmd_delete(args):
    cmd = ["drive", "delete", args.id]
    if args.permanent:
        cmd.append("--permanent")
    p = run_gog(cmd, check=False)
    if p.returncode != 0 and "without --force" in (p.stderr + p.stdout):
        p = run_gog(["--force"] + cmd)
    elif p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    d = parse_kv_plain(p.stdout)
    print(json.dumps({"ok": True, "id": d.get("id", args.id), "trashed": d.get("trashed"), "deleted": d.get("deleted")}))


def cmd_move(args):
    p = run_gog(["drive", "move", args.id, "--parent", args.parent])
    d = parse_kv_plain(p.stdout)
    print(json.dumps({"ok": True, "id": d.get("id", args.id), "parent": args.parent, "name": d.get("name")}))


def main():
    ap = argparse.ArgumentParser(description="Fast Drive CRUD wrapper on gogcli")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("mkdir")
    p.add_argument("name")
    p.add_argument("--parent", default="root")
    p.set_defaults(func=cmd_mkdir)

    p = sub.add_parser("ls")
    p.add_argument("--parent", default="root")
    p.add_argument("--max", type=int, default=100)
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("doc")
    p.add_argument("title")
    p.add_argument("--parent", default="root")
    p.add_argument("--parent-name")
    p.add_argument("--parent-base", default="root")
    p.add_argument("--content")
    p.add_argument("--file")
    p.add_argument("--markdown", action="store_true")
    p.set_defaults(func=cmd_doc)

    p = sub.add_parser("move")
    p.add_argument("id")
    p.add_argument("parent")
    p.set_defaults(func=cmd_move)

    p = sub.add_parser("delete")
    p.add_argument("id")
    p.add_argument("--permanent", action="store_true")
    p.set_defaults(func=cmd_delete)

    args = ap.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
