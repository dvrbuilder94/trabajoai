"""Collect job postings from public Greenhouse and Lever APIs; never applies."""
import hashlib, html, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))["sources"]
OUTPUT = ROOT / "data/jobs.json"
HEADERS = {"User-Agent": "TrabajoAI/0.1 (personal job research)", "Accept": "application/json"}
POSITIVE = {"strategy": 18, "strategic": 12, "business development": 20,
            "partnership": 16, "payments": 17, "fintech": 14, "venture": 15,
            "capital markets": 20, "product strategy": 18, "corporate development": 19,
            "latam": 8, "latin america": 8, "spanish": 9, "financial": 7,
            "expansion": 12, "growth": 5, "m&a": 15, "commercial": 7}
EXCLUDE = ("software engineer", "site reliability", "nurse", "physician", "internship", "recruiter")

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def plain(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()

def format_job(company, external_id, title, location, description, url, date=""):
    if not url.startswith("https://"):
        return None
    title_l, desc_l = title.lower(), description.lower()
    hits = [k for k in POSITIVE if k in title_l or k in desc_l]
    score = 0 if any(k in title_l for k in EXCLUDE) else min(
        99, 15 + sum(w if k in title_l else min(5, w//3) for k,w in POSITIVE.items() if k in hits))
    remote = bool(re.search(r"\bremote\b|work from anywhere", title+" "+location, re.I))
    return {"id": hashlib.sha256(f"{company}:{external_id}".encode()).hexdigest()[:20],
            "company": company, "title": title, "location": location,
            "description": description[:7000], "url": url, "posted_at": str(date)[:10],
            "work_type": "remote" if remote else "other", "score": score,
            "reason": "Coincidencias: " + (", ".join(hits[:5]) if hits else "limitadas"),
            "salary": "", "verification": "Public ATS listing; work eligibility unverified"}

def collect(source):
    kind, slug, company = source["type"], urllib.parse.quote(source["slug"], safe=""), source["company"]
    if kind == "greenhouse":
        data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
        for j in data.get("jobs", []):
            yield format_job(company, j.get("id"), j.get("title",""),
                (j.get("location") or {}).get("name",""), plain(j.get("content","")),
                j.get("absolute_url",""), j.get("updated_at",""))
    elif kind == "lever":
        data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        for j in data:
            yield format_job(company, j.get("id"), j.get("text",""),
                (j.get("categories") or {}).get("location",""),
                plain(j.get("descriptionPlain") or j.get("description","")), j.get("hostedUrl",""))
    else:
        raise ValueError(f"Unknown source type: {kind}")

def main():
    jobs, successes, failures = {}, 0, []
    for source in SOURCES:
        try:
            batch = [j for j in collect(source) if j]
            for job in batch:
                jobs[job["id"]] = job
            successes += 1
            print(source["company"], len(batch))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            failures.append(source["company"])
            print("FAILED", source["company"], str(exc), file=sys.stderr)
    if not successes:
        print("All sources failed; preserving previous jobs.json", file=sys.stderr)
        return 1
    result = sorted(jobs.values(), key=lambda j: j["score"], reverse=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Saved {len(result)} public postings; failed sources: {', '.join(failures) or 'none'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
