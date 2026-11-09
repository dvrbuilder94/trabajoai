"""Import public ATS listings from data/jobs.json into Supabase (server-side only).

Required GitHub Actions secrets:
  SUPABASE_URL=https://<project-ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=<secret key, never publish>
If missing, this script safely exits without changing the DB.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data/jobs.json"
URL = os.getenv("SUPABASE_URL", "").rstrip("/")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
CHUNK = 100

def normalize(item, timestamp):
    url = item.get("url", "")
    if not isinstance(url, str) or not url.startswith("https://"):
        return None
    # A generic remote listing (especially US-remote) does not imply Chile eligibility.
    loc = str(item.get("location") or "")
    chile = bool(re.search(r"\bchile\b|\bsantiago\b", loc, re.I))
    latam = bool(re.search(r"latin america|\blatam\b", loc, re.I))
    if not (chile or latam):
        return None
    date = str(item.get("posted_at") or "")[:10]
    if not date or len(date) != 10:
        date = None
    return {
        "id": str(item["id"]),
        "source": "public_ats",
        "company": str(item.get("company") or ""),
        "title": str(item.get("title") or ""),
        "location": str(item.get("location") or ""),
        "description": str(item.get("description") or "")[:7000],
        "url": url,
        "posted_at": date,
        "last_seen_at": timestamp,
        "score": min(100, max(0, int(item.get("score") or 0))),
        "work_type": str(item.get("work_type") or "unknown"),
        "salary_text": str(item.get("salary") or ""),
        "verification": "Detectada en API oficial de ofertas; enlace individual y elegibilidad pendientes de confirmar",
        "metadata": {
            "reason": str(item.get("reason") or ""),
            "geo_eligibility": "confirmed" if chile else "needs_confirmation",
            "availability_status": "ats_listed",
            "location_category": ("remote_chile" if chile and str(item.get("work_type")) == "remote" else "santiago" if re.search(r"\\bsantiago\\b", loc, re.I) else "unknown"),
            "work_arrangement": "remote" if str(item.get("work_type")) == "remote" else "unknown",
            "checked_at": timestamp[:10],
            "remote_from_chile": "confirmed" if chile and str(item.get("work_type")) == "remote" else "unknown",
            "visa_sponsorship": "unknown",
            "source_type": "public_ats",
        },
    }

def main():
    if not URL or not KEY:
        print("INFO: Supabase secret not configured; skipping sync. Public JSON remains available.")
        return 0
    if not URL.startswith("https://") or "supabase.co" not in URL:
        raise RuntimeError("Invalid Supabase URL")
    jobs = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(jobs, list):
        raise RuntimeError("jobs.json must contain an array")
    if not jobs:
        print("INFO: jobs.json empty. Will not modify existing database data.")
        return 0
    now = datetime.now(timezone.utc).isoformat()
    rows = [r for j in jobs if (r := normalize(j, now))]
    if not rows:
        print("No postings with explicit Chile/LATAM location evidence; leaving database unchanged")
        return 0
    endpoint = URL + "/rest/v1/job_listings?on_conflict=id"
    headers = {
        "apikey": KEY,
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
        "User-Agent": "TrabajoAI-job-sync/0.1",
    }
    count = 0
    for start in range(0, len(rows), CHUNK):
        batch = rows[start:start + CHUNK]
        request = urllib.request.Request(
            endpoint, data=json.dumps(batch).encode("utf-8"),
            headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status not in (200, 201, 204):
                    raise RuntimeError("Supabase returned HTTP " + str(response.status))
        except urllib.error.HTTPError as exc:
            print("Supabase sync failed with HTTP " + str(exc.code), file=sys.stderr)
            return 1
        count += len(batch)
    print(f"Synced {count} public listings to Supabase")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
