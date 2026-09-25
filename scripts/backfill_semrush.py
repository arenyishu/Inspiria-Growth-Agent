from extractors.semrush_client import fetch_semrush_data
from database.db_manager import upsert_semrush_data

print("Backfilling SEMrush data...")
df = fetch_semrush_data("2023-01-01", "2026-09-30")
upsert_semrush_data(df)
print("SEMrush backfill complete!")
