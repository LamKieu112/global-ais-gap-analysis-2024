"""Reproduce the 1,923-event set of GFW AIS gap events (January 2024) from events_raw_1.csv.

Usage:  python reproduce_1923.py events_raw_1.csv gfw_clean_1923_global.csv
Needs:  pandas (pip install pandas)
"""
import sys
import pandas as pd

src = sys.argv[1] if len(sys.argv) > 1 else "events_raw_1.csv"
dst = sys.argv[2] if len(sys.argv) > 2 else "gfw_clean_1923_global.csv"

# Read vessel_ssvid as a string so leading zeros are kept
df = pd.read_csv(src, dtype={"vessel_ssvid": str}, low_memory=False)
t0 = pd.to_datetime(df["start"], format="mixed", utc=True, errors="coerce")
s = df["vessel_ssvid"].fillna("")
mid = pd.to_numeric(s.str[:3], errors="coerce")

steps = [
    ("1. Raw data",                                              pd.Series(True, index=df.index)),
    ("2. start in January 2024 (UTC)",                           (t0 >= "2024-01-01") & (t0 < "2024-02-01")),
    ("3. Exclude vessel_type = gear",                            df["vessel_type"] != "gear"),
    ("4. ssvid has 9 digits and does not start with 99",         s.str.fullmatch(r"\d{9}") & ~s.str.startswith("99")),
    ("5. gap_impliedSpeedKnots <= 30",                           df["gap_impliedSpeedKnots"] <= 30),
    ("6. gap_durationHours <= 720 (30 days)",                    df["gap_durationHours"] <= 720),
    ("7. Exclude ssvid starting with 98 (auxiliary craft/buoys)", ~s.str.startswith("98")),
    ("8. MID (first 3 digits of ssvid) in 201-775 (valid ITU)",  mid.between(201, 775)),
]
mask, prev, rows = pd.Series(True, index=df.index), None, []
for name, cond in steps:
    mask &= cond
    n = int(mask.sum())
    rows.append((name, n, "" if prev is None else prev - n, round(n / len(df) * 100, 2)))
    prev = n
out = pd.DataFrame(rows, columns=["step", "rows_remaining", "rows_removed", "pct_of_raw"])
print(out.to_string(index=False))
df[mask].to_csv(dst, index=False)
print(f"\nSaved {int(mask.sum()):,} rows -> {dst}")
assert int(mask.sum()) == 1923, "Final row count is not 1,923 - check the input data"
out.to_csv("funnel_46823_to_1923.csv", index=False)
