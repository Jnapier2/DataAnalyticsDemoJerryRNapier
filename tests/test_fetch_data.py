from __future__ import annotations

import csv
import io
import unittest
from urllib.parse import parse_qs, urlparse

from scripts import fetch_data


class FetchDataContractTests(unittest.TestCase):
    @staticmethod
    def csv_bytes(*dates: str) -> bytes:
        zip_codes = ("60607", "60610", "60622")
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fetch_data.FIELDS)
        writer.writeheader()
        for index, (zip_code, inspection_date) in enumerate(
            zip(zip_codes, dates), start=1
        ):
            writer.writerow(
                {
                    "inspection_id": f"TEST-{index}",
                    "facility_type": "Restaurant",
                    "risk": "Risk 1 (High)",
                    "zip": zip_code,
                    "inspection_date": inspection_date,
                    "inspection_type": "Canvass",
                    "results": "Pass",
                }
            )
        return output.getvalue().encode("utf-8")

    def test_query_contains_inclusive_start_and_exclusive_end(self) -> None:
        query = parse_qs(urlparse(fetch_data.build_url()).query)

        self.assertEqual(
            query["$where"],
            [
                "zip in (60607,60610,60622) "
                "and inspection_date >= '2010-01-05T00:00:00.000' "
                "and inspection_date < '2018-06-14T00:00:00.000'"
            ],
        )

    def test_date_boundaries_are_accepted(self) -> None:
        content = self.csv_bytes(
            "2010-01-05T00:00:00.000",
            "2014-01-01T12:00:00.000",
            "2018-06-13T23:59:59.999",
        )

        row_count, checksum = fetch_data.validate_csv(content)

        self.assertEqual(row_count, 3)
        self.assertEqual(len(checksum), 64)

    def test_date_before_inclusive_start_is_rejected(self) -> None:
        content = self.csv_bytes(
            "2010-01-04T23:59:59.999",
            "2014-01-01T12:00:00.000",
            "2018-06-13T23:59:59.999",
        )

        with self.assertRaisesRegex(ValueError, "Out-of-scope date at CSV line 2"):
            fetch_data.validate_csv(content)

    def test_date_at_exclusive_end_is_rejected(self) -> None:
        content = self.csv_bytes(
            "2010-01-05T00:00:00.000",
            "2014-01-01T12:00:00.000",
            "2018-06-14T00:00:00.000",
        )

        with self.assertRaisesRegex(ValueError, "Out-of-scope date at CSV line 4"):
            fetch_data.validate_csv(content)


if __name__ == "__main__":
    unittest.main()
