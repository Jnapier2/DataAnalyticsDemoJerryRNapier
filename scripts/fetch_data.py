"""Fetch and validate the bounded Chicago food-inspection snapshot."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import os
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ENDPOINT = "https://data.cityofchicago.org/resource/4ijn-s7e5.csv"
FIELDS = (
    "inspection_id",
    "facility_type",
    "risk",
    "zip",
    "inspection_date",
    "inspection_type",
    "results",
)
ZIP_CODES = {"60607", "60610", "60622"}
END_EXCLUSIVE = datetime.fromisoformat("2018-06-14T00:00:00.000")
ROW_LIMIT = 50_000
DEFAULT_OUTPUT = Path("data/food_inspections_2010_2018.csv.gz")


def build_url() -> str:
    """Return the complete, bounded Socrata query URL."""

    parameters = {
        "$select": ",".join(FIELDS),
        "$where": (
            "zip in (60607,60610,60622) "
            "and inspection_date < '2018-06-14T00:00:00.000'"
        ),
        "$order": "inspection_id",
        "$limit": str(ROW_LIMIT),
    }
    return f"{API_ENDPOINT}?{urlencode(parameters)}"


def fetch_csv(timeout: int) -> bytes:
    """Download the CSV with an explicit user agent and timeout."""

    request = Request(
        build_url(),
        headers={"User-Agent": "Jerry-Napier-food-inspection-study/2026"},
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def validate_csv(content: bytes) -> tuple[int, str]:
    """Validate schema, identifiers, ZIP scope, and study-period boundary."""

    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError(f"Unexpected CSV header: {reader.fieldnames!r}")

    identifiers: set[str] = set()
    row_count = 0
    observed_zips: set[str] = set()

    for line_number, row in enumerate(reader, start=2):
        row_count += 1
        inspection_id = row["inspection_id"].strip()
        if not inspection_id or inspection_id in identifiers:
            raise ValueError(
                f"Missing or duplicate inspection_id at CSV line {line_number}"
            )
        identifiers.add(inspection_id)

        zip_code = row["zip"].strip()
        if zip_code not in ZIP_CODES:
            raise ValueError(f"Out-of-scope ZIP code at CSV line {line_number}")
        observed_zips.add(zip_code)

        inspection_date = datetime.fromisoformat(row["inspection_date"].strip())
        if inspection_date >= END_EXCLUSIVE:
            raise ValueError(f"Out-of-scope date at CSV line {line_number}")

    if not row_count or row_count >= ROW_LIMIT:
        raise ValueError(f"Unexpected row count: {row_count}")
    if observed_zips != ZIP_CODES:
        raise ValueError(f"Incomplete ZIP-code coverage: {sorted(observed_zips)}")

    return row_count, hashlib.sha256(content).hexdigest()


def write_snapshot(content: bytes, output: Path) -> None:
    """Atomically replace the gzip snapshot with deterministic metadata."""

    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(file_descriptor, "wb") as raw_file:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw_file, mtime=0
            ) as compressed_file:
                compressed_file.write(content)
        os.replace(temporary_name, output)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch the fixed-period Chicago food-inspection extract."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the live response without replacing the local snapshot",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content = fetch_csv(args.timeout)
    row_count, checksum = validate_csv(content)
    if not args.check_only:
        write_snapshot(content, args.output)
    action = "validated" if args.check_only else f"wrote {args.output}"
    print(f"{action}: {row_count:,} rows; sha256={checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
