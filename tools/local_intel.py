#!/usr/bin/env python3
import argparse, json, os, urllib.parse, urllib.request

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


def brave_search(query: str, count: int = 8, country: str = "US"):
    key = os.getenv("BRAVE_API_KEY")
    if not key:
        raise RuntimeError("BRAVE_API_KEY missing. Export it in shell env for local script use.")
    params = urllib.parse.urlencode({
        "q": query,
        "count": count,
        "country": country,
        "search_lang": "en",
        "safesearch": "moderate",
    })
    req = urllib.request.Request(f"{BRAVE_ENDPOINT}?{params}", headers={"X-Subscription-Token": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def main():
    ap = argparse.ArgumentParser(description="Quick local intel via Brave Search API")
    ap.add_argument("query", help="What to search for")
    ap.add_argument("--near", help="City/area context", default="")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    q = f"{args.query} near {args.near}".strip() if args.near else args.query
    data = brave_search(q, count=args.count)
    results = (data.get("web") or {}).get("results") or []

    out = {
        "query": q,
        "count": len(results),
        "results": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "description": r.get("description"),
            }
            for r in results
        ],
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Local Intel: {q} ({len(results)} results)")
        for i, r in enumerate(out["results"], 1):
            print(f"{i}. {r['title']}\n   {r['url']}\n   {r['description'] or ''}\n")


if __name__ == "__main__":
    main()
