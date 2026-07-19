# Data provenance

`food_inspections_2010_2018.csv.gz` is a bounded snapshot of the City of Chicago [Food Inspections dataset](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5), dataset identifier `4ijn-s7e5`.

## Scope

- Retrieved: July 19, 2026
- Unit: one food-inspection record
- ZIP codes: 60607, 60610, and 60622
- Date filter: `inspection_date < 2018-06-14T00:00:00.000`
- Sort order: `inspection_id`
- Rows: 13,333
- Selected fields: `inspection_id`, `facility_type`, `risk`, `zip`, `inspection_date`, `inspection_type`, `results`
- SHA-256 of the uncompressed CSV: `fa83366082b4605aff809c788b72e8b00e5f33fa585baddf1c40510dea48e4e0`

The date boundary preserves the original project's last observed inspection date. The source may revise historical records; the 2018 notebook reported 12,971 rows, while this snapshot contains 13,333. Because the original CSV is absent, the exact revisions cannot be reconstructed.

## Retrieval

Run the deterministic retrieval script from the repository root:

```bash
python scripts/fetch_data.py
```

The script validates the header, row identifiers, ZIP-code scope, and date boundary before replacing the snapshot. It prints the row count and SHA-256 checksum needed to update this file.

The City of Chicago's terms apply to the source data. This repository does not grant a separate license for the snapshot.
