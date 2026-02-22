#!/usr/bin/env python3
import argparse, json, os, re, urllib.parse, urllib.request

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
POS = {"best","reliable","top","fast","durable","affordable","great","recommended"}
NEG = {"bad","issue","problem","complaint","lawsuit","expensive","slow","avoid"}


def brave_search(query: str, count: int = 6):
    key = os.getenv("BRAVE_API_KEY")
    if not key:
        raise RuntimeError("BRAVE_API_KEY missing. Export it in shell env for local script use.")
    params = urllib.parse.urlencode({"q": query, "count": count, "country": "US", "search_lang": "en"})
    req = urllib.request.Request(f"{BRAVE_ENDPOINT}?{params}", headers={"X-Subscription-Token": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def score_snippet(text: str):
    t = re.findall(r"[a-zA-Z]+", (text or "").lower())
    s = 0
    for w in t:
        if w in POS: s += 1
        if w in NEG: s -= 1
    return s


def main():
    ap = argparse.ArgumentParser(description="Decision support from web snippets")
    ap.add_argument("--question", required=True)
    ap.add_argument("--option", action="append", required=True, help="Repeat per option")
    ap.add_argument("--near", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    for opt in args.option:
        q = f"{opt} {args.question} {('near ' + args.near) if args.near else ''}".strip()
        data = brave_search(q, count=6)
        hits = (data.get("web") or {}).get("results") or []
        snippets = [h.get("description") or "" for h in hits]
        score = sum(score_snippet(s) for s in snippets)
        results.append({
            "option": opt,
            "score": score,
            "top_sources": [h.get("url") for h in hits[:3]],
            "notes": [s for s in snippets[:3] if s],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    out = {"question": args.question, "near": args.near, "ranked": results}

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Decision Support: {args.question}")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['option']} (score {r['score']})")
            for u in r["top_sources"]:
                if u: print(f"   - {u}")


if __name__ == "__main__":
    main()
