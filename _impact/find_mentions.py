"""
Find new peer-reviewed papers that mention GlobalArchive, The Fish Collective
or CheckEM, and add them to _data/publications.yml for review.

Searches OpenAlex (titles, abstracts and full text). Run daily by
.github/workflows/find-impact.yml, which opens a pull request with any new finds.

Run locally from the repo root:  python _impact/find_mentions.py
  --dry-run   print what would be added without changing any files

Optional environment variables:
  OPENALEX_API_KEY  free key from https://openalex.org/settings/api (raises the daily limit)
  OPENALEX_MAILTO   contact email sent to OpenAlex
"""

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import yaml

DATA_FILE = "_data/publications.yml"
SEEN_FILE = "_impact/seen.txt"          # every DOI/ID ever proposed, so rejected ones don't come back
SUMMARY_FILE = os.environ.get("IMPACT_SUMMARY", "_impact/last-run.md")  # pull request description (kept outside the repo in Actions)

# label shown on the website  ->  OpenAlex search query
SEARCHES = {
    "GlobalArchive": '"GlobalArchive" OR "globalarchive.org" OR ("Global Archive" AND (BRUV OR BRUVs OR "stereo-video"))',
    "The Fish Collective": '"Fish Collective" AND (BRUV OR BRUVs OR "stereo-video" OR "underwater video" OR GlobalArchive)',
    "CheckEM": '"CheckEM"',
}

# OpenAlex work types and where they go on the Impact page (anything else is skipped)
TYPE_MAP = {
    "article": "paper",
    "review": "paper",
    "letter": "paper",
    "book-chapter": "paper",
    "report": "policy",
}

PER_PAGE = 200
MAX_PAGES = 5
API = "https://api.openalex.org/works"


def get_json(params):
    key = os.environ.get("OPENALEX_API_KEY")
    mailto = os.environ.get("OPENALEX_MAILTO")
    if key:
        params["api_key"] = key
    if mailto:
        params["mailto"] = mailto
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "fishcollective-impact-finder"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # retry on network errors / 429 / 5xx
            if attempt == 3:
                raise
            print(f"  retrying after error: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def search(query):
    results, cursor = [], "*"
    for _ in range(MAX_PAGES):
        data = get_json({
            "search": query,
            "per_page": PER_PAGE,
            "cursor": cursor,
            "select": "id,doi,title,publication_year,type,authorships,primary_location",
        })
        results += data.get("results", [])
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not data.get("results"):
            break
    return results


def norm_doi(doi):
    if not doi:
        return None
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip(), flags=re.I).lower()


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def q(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def first_author(work):
    auths = work.get("authorships") or []
    if not auths:
        return None
    name = (auths[0].get("author") or {}).get("display_name") or auths[0].get("raw_author_name")
    if not name:
        return None
    if len(auths) == 1:
        return name  # keeps organisation names like "Parks Australia" intact
    return f"{name.split()[-1]} et al."


def source_name(work):
    loc = work.get("primary_location") or {}
    return ((loc.get("source") or {}).get("display_name")) or None


def landing_url(work):
    loc = work.get("primary_location") or {}
    return loc.get("landing_page_url") or work.get("id")


def to_yaml(item):
    lines = [f"- type: {item['type']}", f"  title: {q(item['title'])}"]
    for field in ("authors", "year", "journal", "source", "doi", "url"):
        v = item.get(field)
        if v:
            lines.append(f"  {field}: {v if field == 'year' else q(v)}")
    lines.append("  mentions: [" + ", ".join(q(m) for m in item["mentions"]) + "]")
    lines.append(f"  added: {item['added']}")
    return "\n".join(lines) + "\n"


def main():
    dry = "--dry-run" in sys.argv
    existing = yaml.safe_load(open(DATA_FILE, encoding="utf-8")) or []
    known = set()
    for e in existing:
        if e.get("doi"):
            known.add(norm_doi(e["doi"]))
        if e.get("url"):
            known.add(e["url"].strip().lower())
        known.add(norm_title(e.get("title")))
    seen = set()
    if os.path.exists(SEEN_FILE):
        seen = {l.strip().lower() for l in open(SEEN_FILE, encoding="utf-8") if l.strip() and not l.startswith("#")}

    found = {}  # key -> item
    for label, query in SEARCHES.items():
        works = search(query)
        print(f"{label}: {len(works)} results from OpenAlex")
        for w in works:
            section = TYPE_MAP.get(w.get("type"))
            if not section or not w.get("title"):
                continue
            doi = norm_doi(w.get("doi"))
            key = doi or (w.get("id") or "").lower()
            if key in found:
                if label not in found[key]["mentions"]:
                    found[key]["mentions"].append(label)
                continue
            if key in known or key in seen or norm_title(w["title"]) in known:
                continue
            item = {
                "type": section,
                "title": re.sub(r"\s+", " ", w["title"]).strip(),
                "authors": first_author(w),
                "year": w.get("publication_year"),
                "mentions": [label],
                "added": dt.date.today().isoformat(),
            }
            if section == "paper":
                item["journal"] = source_name(w)
            else:
                item["source"] = source_name(w)
            if doi:
                item["doi"] = doi
            else:
                item["url"] = landing_url(w)
            found[key] = item

    new = sorted(found.values(), key=lambda i: -(i.get("year") or 0))
    print(f"{len(new)} new item(s)")
    for i in new:
        print(f"  + [{i['type']}] {i.get('year')} {i['title'][:90]}  ({', '.join(i['mentions'])})")
    if dry:
        return
    os.makedirs(os.path.dirname(SUMMARY_FILE) or ".", exist_ok=True)
    if not new:
        open(SUMMARY_FILE, "w", encoding="utf-8").write("No new mentions found.\n")
        return

    with open(DATA_FILE, "a", encoding="utf-8", newline="") as f:
        f.write("\n# --- Added automatically " + dt.date.today().isoformat() + " (check before merging) ---\n")
        for i in new:
            f.write("\n" + to_yaml(i))

    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        for key in found:
            f.write(key + "\n")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(f"Found **{len(new)}** new item(s) mentioning GlobalArchive, The Fish Collective or CheckEM.\n\n")
        f.write("Delete any false matches from `_data/publications.yml` in this PR before merging. "
                "They won't be suggested again.\n\n")
        for i in new:
            link = f"https://doi.org/{i['doi']}" if i.get("doi") else i.get("url")
            where = i.get("journal") or i.get("source") or ""
            f.write(f"- **{i['title']}**: {i.get('authors') or ''} {i.get('year') or ''}, *{where}* "
                    f"[{i['type']}] ({', '.join(i['mentions'])}) {link}\n")


if __name__ == "__main__":
    main()
