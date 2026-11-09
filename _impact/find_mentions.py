"""
Find new papers and policy documents that mention GlobalArchive, The Fish
Collective or CheckEM, and add them to _data/publications.yml for review.

Searches OpenAlex (papers: titles, abstracts and full text) and, when an
OVERTON_API_KEY is set, Overton (policy and government documents). Run daily by
.github/workflows/find-impact.yml, which opens a pull request with any new finds.

Run locally from the repo root:  python _impact/find_mentions.py
  --dry-run   print what would be added without changing any files

Optional environment variables:
  OPENALEX_API_KEY  free key from https://openalex.org/settings/api (raises the daily limit)
  OPENALEX_MAILTO   contact email sent to OpenAlex
  OVERTON_API_KEY   Overton API key (Overton is skipped without it)
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

# label shown on the website  ->  exact phrases to look for.
# Each phrase is matched exactly (no stemming, no synonyms) in the title,
# abstract or full text, so "Global" on its own never counts.
SEARCHES = {
    "GlobalArchive": ["GlobalArchive", "Global Archive"],
    "The Fish Collective": ["The Fish Collective"],
    "CheckEM": ["CheckEM"],
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
OVERTON_API = "https://app.overton.io/documents.php"
OVERTON_MAX_PAGES = 10


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


def search(phrase):
    results, cursor = [], "*"
    for _ in range(MAX_PAGES):
        data = get_json({
            "filter": f'fulltext.search.exact:"{phrase}"',
            "per_page": PER_PAGE,
            "cursor": cursor,
            "select": "id,doi,title,publication_year,type,authorships,primary_location",
        })
        results += data.get("results", [])
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not data.get("results"):
            break
    return results


def overton_search(phrase):
    """Policy documents in Overton whose full text contains the exact phrase."""
    key = os.environ.get("OVERTON_API_KEY")
    if not key:
        return None
    results = []
    for page in range(1, OVERTON_MAX_PAGES + 1):
        url = OVERTON_API + "?" + urllib.parse.urlencode(
            {"query": f'"{phrase}"', "format": "json", "api_key": key, "page": page})
        req = urllib.request.Request(url, headers={"User-Agent": "fishcollective-impact-finder"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"  retrying Overton after error: {e}", file=sys.stderr)
                time.sleep(10 * (attempt + 1))
        time.sleep(1.2)  # Overton asks for no more than one call per second
        results += data.get("results") or []
        if not (data.get("query") or {}).get("next_page_url"):
            break
    return results


def overton_year(doc):
    for field in ("published_on", "published", "date", "published_date"):
        m = re.match(r"(\d{4})", str(doc.get(field) or ""))
        if m:
            return int(m.group(1))
    m = re.search(r"(?:19|20)\d{2}(?:\s*[-\u2013/]\s*(?:19|20)?(\d{2}))?", doc.get("title") or "")
    if m:  # e.g. "Annual Report 2022-23" -> 2023
        y = int(m.group(0)[:4])
        return int(str(y)[:2] + m.group(1)) if m.group(1) else y
    return None


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
    for field in ("authors", "year", "journal", "source", "doi", "url", "overton_id"):
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
        if e.get("overton_id"):
            known.add("overton:" + str(e["overton_id"]).lower())
        if e.get("type") == "paper":  # policy titles like "Annual Report" repeat, so only match papers by title
            known.add(norm_title(e.get("title")))
    seen = set()
    if os.path.exists(SEEN_FILE):
        seen = {l.strip().lower() for l in open(SEEN_FILE, encoding="utf-8") if l.strip() and not l.startswith("#")}

    found = {}  # key -> item
    hits = []
    for label, phrases in SEARCHES.items():
        for phrase in phrases:
            works = search(phrase)
            print(f'"{phrase}": {len(works)} results from OpenAlex')
            hits += [(label, w) for w in works]
    for label, w in hits:
        section = TYPE_MAP.get(w.get("type"))
        if not section or not w.get("title"):
            continue
        doi = norm_doi(w.get("doi"))
        key = doi or (w.get("id") or "").lower()
        if key in found:
            if label not in found[key]["mentions"]:
                found[key]["mentions"].append(label)
            continue
        if key in known or key in seen or (section == "paper" and norm_title(w["title"]) in known):
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

    for label, phrases in SEARCHES.items():
        for phrase in phrases:
            docs = overton_search(phrase)
            if docs is None:
                print("Overton: skipped (no OVERTON_API_KEY set)")
                break
            print(f'"{phrase}": {len(docs)} results from Overton')
            for d in docs:
                pid = str(d.get("policy_document_id") or "")
                if not pid or not d.get("title"):
                    continue
                key = "overton:" + pid.lower()
                url = d.get("document_url") or d.get("pdf_url") or \
                    f"https://app.overton.io/document.php?policy_document_id={pid}"
                if key in found:
                    if label not in found[key]["mentions"]:
                        found[key]["mentions"].append(label)
                    continue
                if key in known or key in seen or url.strip().lower() in known:
                    continue
                src = d.get("source") or {}
                found[key] = {
                    "type": "policy",
                    "title": re.sub(r"\s+", " ", d["title"]).strip(),
                    "year": overton_year(d),
                    "source": src.get("title"),
                    "url": url,
                    "overton_id": pid,
                    "mentions": [label],
                    "added": dt.date.today().isoformat(),
                }
        else:
            continue
        break

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
        f.write(f"Found **{len(new)}** new item(s) (papers from OpenAlex, policy documents from Overton) mentioning GlobalArchive, The Fish Collective or CheckEM.\n\n")
        f.write("Delete any false matches from `_data/publications.yml` in this PR before merging. "
                "They won't be suggested again.\n\n")
        for i in new:
            link = f"https://doi.org/{i['doi']}" if i.get("doi") else i.get("url")
            where = i.get("journal") or i.get("source") or ""
            f.write(f"- **{i['title']}**: {i.get('authors') or ''} {i.get('year') or ''}, *{where}* "
                    f"[{i['type']}] ({', '.join(i['mentions'])}) {link}\n")


if __name__ == "__main__":
    main()
