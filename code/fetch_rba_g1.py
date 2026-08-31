#!/usr/bin/env python3
"""
Fetch RBA Statistical Table G1, Consumer Price Inflation.

By default this fetches the current CSV from the RBA statistical tables site.
Use --output-dir for scratch comparisons or --url for a manually archived copy.
"""
import argparse
import csv
import hashlib
import io
import os
import ssl
import tempfile
import urllib.error
import urllib.request

import certifi


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(HERE, "data_raw")
FILENAME = "rba_table_g1.csv"
RBA_G1_URL = "https://www.rba.gov.au/statistics/tables/csv/g1-data.csv"
REQUIRED_SERIES = {"GCPIAGYP", "GCPITXVIYP", "GCPINTIYP"}


def sha16(data):
    return hashlib.sha256(data).hexdigest()[:16]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kells-money-repl/0.1"})
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, timeout=60, context=context) as resp:
            return resp.read(), resp.geturl()
    except urllib.error.URLError as exc:
        raise SystemExit(f"failed to fetch {url}: {exc}") from exc


def validate_csv(filename, data):
    text = data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or not rows[0] or rows[0][0] != "G1 CONSUMER PRICE INFLATION":
        raise SystemExit(f"{filename}: unexpected title row")

    try:
        sid = next(row for row in rows if row and row[0] == "Series ID")
    except StopIteration as exc:
        raise SystemExit(f"{filename}: missing Series ID row") from exc

    missing = sorted(REQUIRED_SERIES - set(sid))
    if missing:
        raise SystemExit(f"{filename}: missing required series IDs: {missing}")

    try:
        pub = next(row for row in rows if row and row[0] == "Publication date")
    except StopIteration:
        pub = []
    pub_dates = sorted(set(cell for cell in pub[1:] if cell))
    data_rows = [row for row in rows[rows.index(sid) + 1 :] if row and row[0]]
    if not data_rows:
        raise SystemExit(f"{filename}: no observations found")

    return len(data_rows), pub_dates


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{os.path.basename(path)}.", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description="Fetch RBA Statistical Table G1 CSV.")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUT,
        help="Directory to write the fetched CSV. Defaults to data_raw/.",
    )
    parser.add_argument(
        "--url",
        default=RBA_G1_URL,
        help="CSV URL to fetch. Defaults to the current RBA G1 table.",
    )
    args = parser.parse_args()

    out_path = os.path.join(args.output_dir, FILENAME)
    old = open(out_path, "rb").read() if os.path.exists(out_path) else None

    data, final_url = fetch(args.url)
    rows, pub_dates = validate_csv(FILENAME, data)
    write_bytes(out_path, data)

    status = "new"
    if old is not None:
        status = "unchanged" if old == data else "changed"
    print(f"{FILENAME}: {status}; {len(data):,} bytes; {rows:,} rows; sha256={sha16(data)}")
    if pub_dates:
        print(f"publication date(s): {', '.join(pub_dates)}")
    print(f"source: {final_url}")


if __name__ == "__main__":
    main()
