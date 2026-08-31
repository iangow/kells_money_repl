#!/usr/bin/env python3
"""
Fetch BIS credit series from FRED.

By default this writes the four CSV files used by script 02 into data_raw/.
Use --output-dir to fetch into a scratch directory for comparison.
"""
import argparse
import hashlib
import os
import tempfile
import urllib.error
import urllib.request


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(HERE, "data_raw")
FRED_GRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

FILES = {
    "bis_fredgraph.csv": [
        "QAUHAM770A", "QATHAM770A", "QBEHAM770A", "QCAHAM770A", "QCHHAM770A",
        "QDEHAM770A", "QDKHAM770A", "QESHAM770A", "QFIHAM770A", "QFRHAM770A",
        "QGBHAM770A",
    ],
    "bis_fredgraph1.csv": [
        "QIEHAM770A", "QITHAM770A", "QJPHAM770A", "QKRHAM770A", "QNLHAM770A",
        "QNOHAM770A", "QNZHAM770A", "QPTHAM770A", "QSEHAM770A", "QUSHAM770A",
    ],
    "bis_fredgraph2.csv": [
        "QAUNAM770A", "QATNAM770A", "QBENAM770A", "QCANAM770A", "QCHNAM770A",
        "QDENAM770A", "QDKNAM770A", "QESNAM770A", "QFINAM770A", "QFRNAM770A",
        "QGBNAM770A",
    ],
    "bis_fredgraph3.csv": [
        "QIENAM770A", "QITNAM770A", "QJPNAM770A", "QKRNAM770A", "QNLNAM770A",
        "QNONAM770A", "QNZNAM770A", "QPTNAM770A", "QSENAM770A", "QUSNAM770A",
    ],
}


def sha16(data):
    return hashlib.sha256(data).hexdigest()[:16]


def fetch(series_ids):
    url = f"{FRED_GRAPH_URL}?id={','.join(series_ids)}"
    req = urllib.request.Request(url, headers={"User-Agent": "kells-money-repl/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise SystemExit(f"failed to fetch {url}: {exc}") from exc


def validate_csv(filename, data, series_ids):
    first_line = data.decode("utf-8-sig").splitlines()[0]
    expected = "observation_date," + ",".join(series_ids)
    if first_line != expected:
        raise SystemExit(
            f"{filename}: unexpected header\n"
            f"expected: {expected}\n"
            f"got:      {first_line}"
        )


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
    parser = argparse.ArgumentParser(description="Fetch BIS credit CSV files from FRED.")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUT,
        help="Directory to write fetched CSV files. Defaults to data_raw/.",
    )
    parser.add_argument(
        "--only",
        choices=FILES.keys(),
        action="append",
        help="Fetch only this output file. May be repeated.",
    )
    args = parser.parse_args()

    selected = args.only or list(FILES)
    for filename in selected:
        series_ids = FILES[filename]
        out_path = os.path.join(args.output_dir, filename)
        old = open(out_path, "rb").read() if os.path.exists(out_path) else None
        data = fetch(series_ids)
        validate_csv(filename, data, series_ids)
        write_bytes(out_path, data)

        status = "new"
        if old is not None:
            status = "unchanged" if old == data else "changed"
        print(f"{filename}: {status}; {len(data):,} bytes; sha256={sha16(data)}")


if __name__ == "__main__":
    main()
