#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime

GOG = "/mnt/c/Users/grant/bin/gogcli/gog.exe"
DEFAULT_ACCOUNT = "grant.m.anderson2021@gmail.com"

PROMO_HINTS = {
    "sale", "discount", "deal", "unsubscribe", "newsletter", "promo", "promotion", "offer", "coupon"
}
IMPORTANT_HINTS = {
    "urgent", "action required", "invoice", "payment", "contract", "closing", "inspection", "meeting", "deadline"
}


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout


def score(thread):
    labels = set(thread.get("labels", []))
    subj = (thread.get("subject") or "").lower()
    sender = (thread.get("from") or "").lower()

    s = 0
    if "IMPORTANT" in labels:
        s += 3
    if "CATEGORY_PRIMARY" in labels:
        s += 2
    if "CATEGORY_UPDATES" in labels:
        s += 1
    if "CATEGORY_PROMOTIONS" in labels:
        s -= 2

    if any(k in subj for k in IMPORTANT_HINTS):
        s += 2
    if any(k in subj for k in PROMO_HINTS):
        s -= 2
    if "no-reply" in sender or "noreply" in sender:
        s -= 1

    return s


def bucket(score_value):
    if score_value >= 3:
        return "read_now"
    if score_value >= 1:
        return "check_soon"
    return "skip_or_batch"


def main():
    ap = argparse.ArgumentParser(description="Fast Gmail daily triage brief")
    ap.add_argument("--account", default=DEFAULT_ACCOUNT)
    ap.add_argument("--query", default="newer_than:1d")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = run([GOG, "-a", args.account, "-j", "gmail", "search", args.query, "--max", str(args.max)])
    data = json.loads(raw)
    threads = data.get("threads", [])

    ranked = []
    for t in threads:
        sc = score(t)
        ranked.append({
            "id": t.get("id"),
            "date": t.get("date"),
            "from": t.get("from"),
            "subject": t.get("subject"),
            "labels": t.get("labels", []),
            "score": sc,
            "bucket": bucket(sc),
        })

    ranked.sort(key=lambda x: (x["score"], x["date"]), reverse=True)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "account": args.account,
        "query": args.query,
        "total": len(ranked),
        "read_now": [r for r in ranked if r["bucket"] == "read_now"],
        "check_soon": [r for r in ranked if r["bucket"] == "check_soon"],
        "skip_or_batch": [r for r in ranked if r["bucket"] == "skip_or_batch"],
    }

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    print(f"Email Brief for {summary['account']} ({summary['query']})")
    print(f"Total: {summary['total']} | Read now: {len(summary['read_now'])} | Check soon: {len(summary['check_soon'])} | Skip/batch: {len(summary['skip_or_batch'])}")

    def show(title, rows, n=8):
        print(f"\n{title}:")
        if not rows:
            print("- none")
            return
        for r in rows[:n]:
            print(f"- [{r['date']}] {r['subject']} — {r['from']} (score {r['score']})")

    show("Read now", summary["read_now"])
    show("Check soon", summary["check_soon"])
    show("Skip/batch", summary["skip_or_batch"])


if __name__ == "__main__":
    main()
