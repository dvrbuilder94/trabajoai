"""Audit job links using the employer's current ATS board, not stale search indexes.

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as server-side Actions secrets.
Conservative: a missing ATS ID must be confirmed on two separate scans
before declaring a posting closed. Any failed board request is inconclusive.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
HEADERS = {"User-Agent": "TrabajoAI-link-audit/1.0", "Accept": "application/json"}
CHECKED = datetime.now(timezone.utc).isoformat()


def request_json(url, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    extra = {"Content-Type": "application/json"} if data is not None else {}
    headers = {**HEADERS, **extra}
    if url.startswith(URL + "/rest/"):
        headers.update({"apikey": KEY, "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(urllib.request.Request(
        url, data=data, method=method, headers=headers), timeout=25) as res:
        if res.status == 204:
            return None
        body = res.read()
        return json.loads(body.decode("utf-8")) if body else None


def locator(url):
    u = urllib.parse.urlparse(url)
    host = u.netloc.lower()
    parts = [urllib.parse.unquote(p) for p in u.path.split("/") if p]
    if host == "jobs.lever.co" and len(parts) >= 2:
        return "lever", parts[0], parts[1].lower()
    if host == "jobs.ashbyhq.com" and len(parts) >= 2:
        return "ashby", parts[0], parts[1].lower()
    if host in ("job-boards.greenhouse.io", "boards.greenhouse.io") and len(parts) >= 3 and parts[-2] == "jobs":
        return "greenhouse", parts[0], parts[-1]
    if host in ("stripe.com", "www.stripe.com"):
        job_id = urllib.parse.parse_qs(u.query).get("gh_jid", [None])[0]
        if job_id:
            return "greenhouse", "stripe", job_id
    if host in ("brex.com", "www.brex.com"):
        job_id = urllib.parse.parse_qs(u.query).get("gh_jid", [None])[0]
        if job_id:
            return "greenhouse", "brex", job_id
    return None


def posting_ids(provider, slug):
    q = urllib.parse.quote(slug, safe="")
    if provider == "lever":
        jobs = request_json(f"https://api.lever.co/v0/postings/{q}?mode=json")
        return {str(j.get("id", "")).lower() for j in jobs}
    if provider == "ashby":
        board = request_json(f"https://api.ashbyhq.com/posting-api/job-board/{q}")
        return {
            urllib.parse.urlparse(j.get("jobUrl") or j.get("applyUrl") or "").path.rstrip("/").split("/")[-1].lower()
            for j in board.get("jobs", []) if j.get("isListed", True)
        }
    if provider == "greenhouse":
        board = request_json(f"https://boards-api.greenhouse.io/v1/boards/{q}/jobs")
        return {str(j.get("id", "")) for j in board.get("jobs", [])}
    return None


def update(row, found):
    meta = dict(row.get("metadata") or {})
    if found:
        meta["not_found_streak"] = 0
        meta["availability_status"] = "verified" if meta.get("availability_status") == "verified" else "ats_listed"
        note = "Cargo presente en cartelera oficial ATS el " + CHECKED[:10] + "; revisar requisitos antes de postular."
    else:
        meta["not_found_streak"] = int(meta.get("not_found_streak") or 0) + 1
        if meta.get("availability_status") == "closed":
            note = "Oferta ya marcada desactualizada; continúa ausente del ATS oficial."
        elif meta["not_found_streak"] >= 2:
            meta["availability_status"] = "closed"
            note = "Cargo ausente en dos revisiones de la cartelera oficial ATS. Enlace posiblemente caducado."
        else:
            meta["availability_status"] = "unverified"
            note = "Cargo ausente de la cartelera ATS actual; se repetirá revisión antes de marcarlo cerrado."
    meta["checked_at"] = CHECKED[:10]
    patch = {"metadata": meta, "verification": note}
    if found:
        patch["last_seen_at"] = CHECKED
    url = URL + "/rest/v1/job_listings?id=eq." + urllib.parse.quote(row["id"], safe="")
    request_json(url, "PATCH", patch)


def main():
    if not URL or not KEY:
        print("Link audit skipped: GitHub Actions Supabase credentials are not configured.")
        return 0
    if not URL.startswith("https://") or not URL.endswith(".supabase.co"):
        raise RuntimeError("Invalid Supabase URL")
    rows = request_json(URL + "/rest/v1/job_listings?select=id,url,metadata&limit=5000")
    boards, counts = {}, {"found": 0, "missing": 0, "inconclusive": 0, "unsupported": 0}
    for row in rows:
        loc = locator(row.get("url") or "")
        if not loc:
            counts["unsupported"] += 1
            continue
        provider, slug, posting_id = loc
        key = (provider, slug.lower())
        if key not in boards:
            try:
                boards[key] = posting_ids(provider, slug)
                print("Board checked:", provider, slug, len(boards[key]), "open postings")
            except (urllib.error.URLError, ValueError, TypeError, KeyError) as error:
                boards[key] = None
                print("Board inaccessible:", provider, slug, str(error)[:120], file=sys.stderr)
        if boards[key] is None:
            counts["inconclusive"] += 1
            continue
        found = posting_id in boards[key]
        update(row, found)
        counts["found" if found else "missing"] += 1
    print("Audit completed:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
