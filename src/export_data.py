from pathlib import Path
import duckdb

SRC_DB = Path.home() / "Downloads/uk-house-price-pipeline/data/warehouse/house_prices.duckdb"
OUT = Path("data")
OUT.mkdir(exist_ok=True)

con = duckdb.connect(str(SRC_DB), read_only=True)
con.execute(f"""
    COPY (
        SELECT
            date_of_transfer AS sale_date,
            sale_year,
            sale_month,
            price,
            postcode_district,
            property_type_label AS property_type,
            build_status,
            tenure,
            town_city,
            district
        FROM clean_ppd
        WHERE is_greater_manchester AND ppd_category_type = 'A'
    ) TO '{OUT}/gm_sales.parquet' (FORMAT parquet)
""")
con.execute(f"COPY (SELECT year, cpi FROM cpi_annual) TO '{OUT}/cpi_annual.parquet' (FORMAT parquet)")

check = duckdb.connect()
n = check.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT}/gm_sales.parquet')").fetchone()[0]
print(f"Exported {n:,} Greater Manchester sales")
for f in sorted(OUT.glob("*.parquet")):
    print(f"{f.name}: {f.stat().st_size / 1e6:.1f} MB")