#!/usr/bin/env python3
"""Download AIS gap ("AIS off") events from the Global Fishing Watch (GFW) Events API v3
and save them as a flat CSV with the same 42 columns as events_raw_1.csv.

Setup
-----
    pip install requests
    export GFW_API_TOKEN="your-token"        # Windows PowerShell: $env:GFW_API_TOKEN="your-token"

Create an API access token in the GFW API portal (account required; check GFW's terms of use):
    https://globalfishingwatch.org/our-apis/

Usage
-----
    python fetch_gfw_gaps.py                                   # January 2024, writes events_raw_1.csv
    python fetch_gfw_gaps.py --start-date 2024-01-01 --end-date 2024-01-31 --out events_raw_1.csv
    python fetch_gfw_gaps.py --save-json raw_pages.jsonl       # also keep the untouched API pages

Notes
-----
* Endpoint:  POST https://gateway.api.globalfishingwatch.org/v3/events?offset=..&limit=..
  Dataset:   public-global-gaps-events:latest
* The API returns a window of events: an event is included when its [start, end] interval
  overlaps [startDate, endDate]. That is why a January 2024 query also returns gaps that began
  years earlier and ended in 2024 or later.
* The token is read only from the GFW_API_TOKEN environment variable and is never printed or saved.
"""
import argparse
import csv
import json
import os
import sys
import time

import requests

BASE_URL = os.environ.get("GFW_BASE_URL", "https://gateway.api.globalfishingwatch.org")
DATASET = "public-global-gaps-events:latest"

# Column order of events_raw_1.csv. Columns not listed here are appended at the end
# (so nothing the API returns is lost); columns the API omits are written as empty.
COLUMNS = [
    "start", "end", "id", "type", "boundingBox", "position_lat", "position_lon",
    "regions_mpa", "regions_eez", "regions_rfmo", "regions_fao", "regions_majorFao",
    "regions_eez12Nm", "regions_highSeas", "regions_mpaNoTakePartial", "regions_mpaNoTake",
    "regions_ebsa", "regions_imma", "regions_dukePaa", "regions_protectedseas", "regions_hsp",
    "regions_fraGfcmFao", "distances_startDistanceFromShoreKm", "distances_endDistanceFromShoreKm",
    "distances_startDistanceFromPortKm", "distances_endDistanceFromPortKm",
    "vessel_id", "vessel_name", "vessel_ssvid", "vessel_flag", "vessel_type", "vessel_nextPort",
    "gap_intentionalDisabling", "gap_distanceKm", "gap_durationHours", "gap_impliedSpeedKnots",
    "gap_positions12HoursBeforeSat", "gap_positionsPerDaySatReception",
    "gap_offPosition_lat", "gap_offPosition_lon", "gap_onPosition_lat", "gap_onPosition_lon",
]


def flatten(obj, prefix=""):
    """Flatten nested dicts into {"a_b_c": value}. Lists and scalars are kept as they are."""
    flat = {}
    for key, value in obj.items():
        name = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten(value, name))
        else:
            flat[name] = value
    return flat


def request_page(session, url, params, body, max_retries, timeout):
    """POST one page, retrying on rate limits (429) and temporary server errors (5xx)."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(url, params=params, json=body, timeout=timeout)
        except requests.RequestException as exc:
            wait = min(60, 2 ** attempt)
            print(f"  network error ({exc.__class__.__name__}); retry {attempt}/{max_retries} in {wait}s")
            time.sleep(wait)
            continue
        if resp.status_code in (200, 201):
            return resp.json()

        if resp.status_code in (429, 500, 502, 503, 504):
            wait = float(resp.headers.get("Retry-After", min(60, 2 ** attempt)))
            print(f"  HTTP {resp.status_code}; retry {attempt}/{max_retries} in {wait:.0f}s")
            time.sleep(wait)
            continue
        if resp.status_code in (401, 403):
            sys.exit(f"Authentication failed (HTTP {resp.status_code}). Check GFW_API_TOKEN and that it is still valid.")
        sys.exit(f"Request failed: HTTP {resp.status_code}: {resp.text[:300]}")
    sys.exit("Giving up after repeated errors. Re-run later; nothing was written.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start-date", default="2024-01-01", help="window start, YYYY-MM-DD (default 2024-01-01)")
    ap.add_argument("--end-date", default="2024-01-31", help="window end, YYYY-MM-DD (default 2024-01-31)")
    ap.add_argument("--dataset", default=DATASET)
    ap.add_argument("--limit", type=int, default=1000, help="events per page (default 1000)")
    ap.add_argument("--sort", default="+start", help="sort order, e.g. +start, -start, +end, -end")
    ap.add_argument("--all-gaps", action="store_true",
                    help="keep every gap. By default only gaps flagged intentionalDisabling = true are kept "
                         "(this matches events_raw_1.csv, where all rows are True)")
    ap.add_argument("--out", default="events_raw_1.csv")
    ap.add_argument("--save-json", default=None, help="optional .jsonl file to store each raw API page")
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=120, help="seconds per request")
    args = ap.parse_args()

    token = os.environ.get("GFW_API_TOKEN")
    if not token:
        sys.exit("GFW_API_TOKEN is not set. Export it first (see the top of this file).")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

    url = f"{BASE_URL}/v3/events"
    body = {"datasets": [args.dataset], "startDate": args.start_date, "endDate": args.end_date}
    if not args.all_gaps:
        body["gapIntentionalDisabling"] = True   # the filter is also enforced client-side below

    rows, seen_ids = [], set()
    offset, total, pages, dropped_dup, dropped_flag = 0, None, 0, 0, 0
    raw_fh = open(args.save_json, "w", encoding="utf-8") if args.save_json else None
    print(f"Downloading {args.dataset}  {args.start_date} -> {args.end_date}  (page size {args.limit})")
    try:
        while True:
            page = request_page(session, url, {"offset": offset, "limit": args.limit, "sort": args.sort},
                                body, args.max_retries, args.timeout)
            pages += 1
            entries = page.get("entries") or []
            total = page.get("total", total)
            if raw_fh:
                raw_fh.write(json.dumps(page, ensure_ascii=False) + "\n")
            for entry in entries:
                if entry.get("id") in seen_ids:
                    dropped_dup += 1
                    continue
                seen_ids.add(entry.get("id"))
                flat = flatten(entry)
                if not args.all_gaps and str(flat.get("gap_intentionalDisabling")).lower() != "true":
                    dropped_flag += 1
                    continue
                rows.append(flat)
            print(f"  page {pages}: +{len(entries)} entries  (kept {len(rows):,} / total reported {total})")
            next_offset = page.get("nextOffset")
            if not entries or next_offset is None or next_offset <= offset:
                break
            if total is not None and next_offset >= total:
                break
            offset = next_offset
    finally:
        if raw_fh:
            raw_fh.close()

    if not rows:
        sys.exit("No events returned. Check the date range, dataset name and token permissions.")

    extra = sorted({k for r in rows for k in r} - set(COLUMNS))
    if extra:
        print(f"Note: {len(extra)} column(s) not in events_raw_1.csv were appended at the end: {', '.join(extra)}")
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS + extra, extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows):,} rows x {len(COLUMNS) + len(extra)} columns -> {args.out}")
    if dropped_dup:
        print(f"  duplicates removed (same id): {dropped_dup}")
    if dropped_flag:
        print(f"  gaps skipped because intentionalDisabling was not true: {dropped_flag}")
    if total is not None and total != len(rows) + dropped_dup + dropped_flag:
        print(f"  WARNING: API reported total={total} but {len(rows) + dropped_dup + dropped_flag} entries were received.")


if __name__ == "__main__":
    main()
