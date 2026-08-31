#!/usr/bin/env python3
"""
Fetch OECD SDMX CSV inputs.

By default this refreshes the three OECD raw files used by scripts 02 and 04.
Use --only to fetch a single file, or --output-dir for scratch comparisons.
"""
import argparse
import csv
import hashlib
import io
import os
import tempfile
import urllib.error
import urllib.request


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(HERE, "data_raw")
BASE_URL = "https://sdmx.oecd.org/public/rest/data"

FILES = {
    "oecd_house_prices_raw.csv": {
        "url": (
            f"{BASE_URL}/OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES,1.0/"
            "....?startPeriod=1970&dimensionAtObservation=AllDimensions&format=csvfile"
        ),
        "header": [
            "DATAFLOW", "REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "TIME_PERIOD",
            "OBS_VALUE", "OBS_STATUS", "UNIT_MULT", "ADJUSTMENT", "DECIMALS", "BASE_PER",
        ],
        "required_measures": {"HPI_RPI", "HPI", "RPI"},
    },
    "oecd_cpi_goods_services.csv": {
        "url": (
            f"{BASE_URL}/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/"
            ".A..CPI..GD+SERV+_T.."
            "?startPeriod=2015&endPeriod=2025&dimensionAtObservation=AllDimensions&format=csvfile"
        ),
        "header": [
            "DATAFLOW", "REF_AREA", "FREQ", "METHODOLOGY", "MEASURE", "UNIT_MEASURE",
            "EXPENDITURE", "ADJUSTMENT", "TRANSFORMATION", "TIME_PERIOD", "OBS_VALUE",
            "OBS_STATUS", "UNIT_MULT", "BASE_PER", "DURABILITY", "DECIMALS",
        ],
        "required_expenditures": {"GD", "SERV", "_T"},
    },
    "oecd_household_dashboard.csv": {
        "url": (
            f"{BASE_URL}/OECD.SDD.NAD,DSD_HHDASH@DF_HHDASH_INDIC,1.0/"
            "?startPeriod=2015&endPeriod=2024&dimensionAtObservation=AllDimensions&format=csvfile"
        ),
        "header": [
            "DATAFLOW", "FREQ", "REF_AREA", "MEASURE", "UNIT_MEASURE", "TIME_PERIOD",
            "OBS_VALUE", "ADJUSTMENT", "SECTOR", "ACCOUNTING_ENTRY", "TRANSACTION",
            "INSTR_ASSET", "PRICE_BASE", "TRANSFORMATION", "REF_YEAR_PRICE", "BASE_PER",
            "CONF_STATUS", "DECIMALS", "OBS_STATUS", "UNIT_MULT",
        ],
        "required_measures": {"B6GS1M_R_POP_GR", "B1GQ_R_POP_GR", "B8GS1M_B6GA"},
    },
}


def sha16(data):
    return hashlib.sha256(data).hexdigest()[:16]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kells-money-repl/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read(), resp.geturl()
    except urllib.error.URLError as exc:
        raise SystemExit(f"failed to fetch {url}: {exc}") from exc


def validate_csv(filename, data, spec):
    text = data.decode("utf-8-sig")
    if text.startswith("NoRecordsFound"):
        raise SystemExit(f"{filename}: OECD returned NoRecordsFound")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != spec["header"]:
        raise SystemExit(
            f"{filename}: unexpected header\n"
            f"expected: {','.join(spec['header'])}\n"
            f"got:      {','.join(reader.fieldnames or [])}"
        )

    rows = 0
    measures = set()
    expenditures = set()
    for row in reader:
        rows += 1
        if "MEASURE" in row:
            measures.add(row["MEASURE"])
        if "EXPENDITURE" in row:
            expenditures.add(row["EXPENDITURE"])

    if rows == 0:
        raise SystemExit(f"{filename}: OECD returned only a header")
    missing_measures = spec.get("required_measures", set()) - measures
    if missing_measures:
        raise SystemExit(f"{filename}: missing required measures: {sorted(missing_measures)}")
    missing_expenditures = spec.get("required_expenditures", set()) - expenditures
    if missing_expenditures:
        raise SystemExit(f"{filename}: missing required expenditures: {sorted(missing_expenditures)}")
    return rows


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
    parser = argparse.ArgumentParser(description="Fetch OECD SDMX CSV input files.")
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
        spec = FILES[filename]
        out_path = os.path.join(args.output_dir, filename)
        old = open(out_path, "rb").read() if os.path.exists(out_path) else None

        data, final_url = fetch(spec["url"])
        rows = validate_csv(filename, data, spec)
        write_bytes(out_path, data)

        status = "new"
        if old is not None:
            status = "unchanged" if old == data else "changed"
        print(f"{filename}: {status}; {len(data):,} bytes; {rows:,} rows; sha256={sha16(data)}")
        print(f"source: {final_url}")


if __name__ == "__main__":
    main()
