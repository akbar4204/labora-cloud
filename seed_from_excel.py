from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from supabase import create_client

TABLE_MAPPINGS = {
    "dokumen_inti": "dokumen_inti",
    "inventaris_kebutuhan": "inventaris_kebutuhan",
    "sop": "sop",
    "modul_k3": "modul_k3",
    "instruksi_kerja": "instruksi_kerja",
    "logbook": "logbook",
    "evaluasi": "evaluasi",
    "panduan": "panduan",
}

COLUMN_RENAMES = {
    "PIC": "pic",
    "APD_wajib": "apd_wajib",
    "temuan/kendala": "temuan_kendala",
}


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python seed_from_excel.py <excel_path> <supabase_url> <service_role_key>")
        return 1

    excel_path = Path(sys.argv[1])
    supabase_url = sys.argv[2]
    service_key = sys.argv[3]

    if not excel_path.exists():
        print(f"Excel file not found: {excel_path}")
        return 1

    client = create_client(supabase_url, service_key)
    workbook = pd.read_excel(excel_path, sheet_name=None)

    for sheet_name, table_name in TABLE_MAPPINGS.items():
        df = workbook.get(sheet_name)
        if df is None or df.empty:
            print(f"Skip empty sheet: {sheet_name}")
            continue
        records = df.rename(columns=COLUMN_RENAMES).fillna("").to_dict(orient="records")
        if table_name == "panduan":
            for idx, row in enumerate(records, start=1):
                row["urutan"] = idx
        client.table(table_name).upsert(records).execute()
        print(f"Seeded {table_name}: {len(records)} rows")

    print("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
