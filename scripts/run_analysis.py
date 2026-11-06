"""Rebuild the retail diagnostic with Python's standard library and SQLite."""
import argparse
import csv
from datetime import date, time
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SQL - Retail Sales Analysis_utf .csv"
HEADERS = ["transactions_id", "sale_date", "sale_time", "customer_id", "gender", "age",
           "category", "quantiy", "price_per_unit", "cogs", "total_sale"]


def money(text):
    value = Decimal(text)
    if not value.is_finite() or value < 0 or value * 100 != (value * 100).to_integral_value():
        raise ValueError("Money must be finite, nonnegative and have at most two decimals")
    return int(value * 100)


def normalize(row):
    try:
        tx = int(row["transactions_id"])
        day = date.fromisoformat(row["sale_date"])
        clock = time.fromisoformat(row["sale_time"])
        customer, category = row["customer_id"].strip(), row["category"].strip()
        quantity = int(row["quantiy"])
        price, revenue = money(row["price_per_unit"]), money(row["total_sale"])
        if tx <= 0 or not customer or not category or quantity <= 0:
            raise ValueError("Invalid key, category or quantity")
        if revenue != quantity * price:
            return None, "revenue differs from quantity times price"
        return (tx, day.isoformat(), clock.isoformat(), customer, category, quantity, price, revenue), ""
    except (ValueError, KeyError, InvalidOperation):
        return None, "missing or invalid revenue inputs"


def load_source(connection, path=SOURCE):
    connection.executescript((ROOT / "sql/schema.sql").read_text())
    seen = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADERS:
            raise ValueError("Unexpected source schema or duplicate headers")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Malformed CSV row")
            if row["transactions_id"] in seen:
                raise ValueError("Duplicate transaction ID; resolve before aggregation")
            seen.add(row["transactions_id"])
            clean, reason = normalize(row)
            connection.execute("INSERT INTO raw_sales VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               [row[k] for k in HEADERS] + [int(clean is not None), reason])
            if clean is not None:
                connection.execute("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?)", clean)
    connection.commit()


def query(connection, sql):
    cursor = connection.execute(sql)
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()], columns


def run(output: Path, source: Path = SOURCE):
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(":memory:") as connection:
        load_source(connection, source)
        files = {}
        for path in sorted((ROOT / "sql").glob("0*.sql")):
            rows, fields = query(connection, path.read_text())
            target = output / (path.stem + ".csv")
            with target.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)
            files[path.stem] = rows
        counts = dict(connection.execute("SELECT exclusion_reason, COUNT(*) FROM raw_sales GROUP BY exclusion_reason"))
        source_rows = connection.execute("SELECT COUNT(*) FROM raw_sales").fetchone()[0]
        eligible = connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        ids_gender = connection.execute("SELECT COUNT(*) FROM (SELECT customer_id FROM raw_sales GROUP BY customer_id HAVING COUNT(DISTINCT gender)>1)").fetchone()[0]
        missing_age_retained = connection.execute("SELECT COUNT(*) FROM raw_sales WHERE age='' AND revenue_eligible=1").fetchone()[0]
        annual = files["01_annual_performance"]
        if len(annual) != 2 or [r["year"] for r in annual] != ["2022", "2023"]:
            raise ValueError("This diagnostic requires the documented 2022-2023 source period")
        if len(files["04_monthly_performance"]) != 24:
            raise ValueError("Missing analysis months")
        bridge = files["02_category_growth_bridge"]
        delta = annual[1]["revenue"] - annual[0]["revenue"]
        if abs(sum(r["revenue_change"] for r in bridge) - delta) > .0001:
            raise ValueError("Category bridge does not reconcile")
        for r in bridge:
            if abs(r["revenue_change"] - r["volume_contribution"] - r["ticket_value_contribution"]) > .0001:
                raise ValueError("Volume/value bridge does not reconcile")
        summary = {
            "author": "Grace Ngo", "source_rows": source_rows, "eligible_transactions": eligible,
            "excluded_transactions": source_rows-eligible, "exclusion_counts": {k:v for k,v in counts.items() if k},
            "missing_age_rows_retained": missing_age_retained,
            "customer_ids_with_conflicting_profiles": files["05_identity_quality"][0]["ids_with_conflicting_profiles"],
            "customer_ids_with_conflicting_gender": ids_gender,
            "annual": annual, "category_growth_bridge": bridge,
            "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            "sqlite_version": sqlite3.sqlite_version,
            "limitations": ["Tutorial dataset; real retailer, currency, sampling method and license not documented.",
                            "Customer IDs cannot support reliable retention or demographic targeting.",
                            "COGS unit basis is unknown; profit and margin are not estimated.",
                            "Revenue is observed sample sales; no uplift or causal business impact is claimed."]}
        (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({k: result[k] for k in ["source_rows", "eligible_transactions", "annual"]}, indent=2))


if __name__ == "__main__":
    main()
