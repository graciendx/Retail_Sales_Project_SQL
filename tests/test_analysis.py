import csv
from decimal import Decimal
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.run_analysis import HEADERS, ROOT, SOURCE, load_source, money, normalize, query, run


class RetailTests(unittest.TestCase):
    def row(self, **changes):
        row = dict(zip(HEADERS, ["1", "2023-01-01", "12:30:00", "5", "Female", "", "Beauty", "2", "10.50", "", "21.00"]))
        return row | changes

    def test_missing_age_and_cogs_do_not_remove_valid_revenue(self):
        clean, reason = normalize(self.row())
        self.assertEqual(clean[-1], 2100)
        self.assertEqual(reason, "")

    def test_monetary_identity_violation_is_quarantined(self):
        clean, reason = normalize(self.row(total_sale="22.00"))
        self.assertIsNone(clean)
        self.assertIn("quantity times price", reason)

    def test_invalid_quantity_date_and_infinite_money_are_rejected(self):
        for changes in [{"quantiy": "0"}, {"quantiy": "-1"}, {"sale_date": "2023-02-30"}, {"total_sale": "NaN"}]:
            with self.subTest(changes=changes): self.assertIsNone(normalize(self.row(**changes))[0])

    def test_money_preserves_hundredths(self):
        self.assertEqual(money("10.01"), 1001)
        with self.assertRaises(ValueError): money("10.001")

    def test_duplicate_ids_fail_before_aggregation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.csv"
            with path.open("w") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader(); writer.writerow(self.row()); writer.writerow(self.row())
            with sqlite3.connect(":memory:") as connection:
                with self.assertRaisesRegex(ValueError, "Duplicate transaction"):
                    load_source(connection, path)

    def test_symmetric_bridge_reconciles_with_opposing_drivers(self):
        with sqlite3.connect(":memory:") as connection:
            connection.executescript((ROOT / "sql/schema.sql").read_text())
            rows = [(1,"2022-01-01","12:00","1","A",1,10000,10000),
                    (2,"2023-01-01","12:00","1","A",1,8000,8000),
                    (3,"2023-01-01","12:00","2","A",1,8000,8000)]
            connection.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?)", rows)
            result, _ = query(connection, (ROOT / "sql/02_category_growth_bridge.sql").read_text())
            row = result[0]
            self.assertEqual(row["revenue_change"], 60)
            self.assertEqual(row["volume_contribution"], 90)
            self.assertEqual(row["ticket_value_contribution"], -30)

    def test_full_results_match_independent_source_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run(Path(directory))
            self.assertEqual(result["source_rows"], 2000)
            self.assertEqual(result["eligible_transactions"], 1997)
            self.assertEqual(result["missing_age_rows_retained"], 10)
            self.assertEqual(result["customer_ids_with_conflicting_gender"], 151)
            with (Path(directory) / "05_identity_quality.csv").open() as handle:
                audit = list(csv.DictReader(handle))
            self.assertEqual(len(audit), 1)
            self.assertNotIn("customer_id", audit[0])
            totals = {"2022": Decimal(0), "2023": Decimal(0)}
            with SOURCE.open(encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    if row["total_sale"]: totals[row["sale_date"][:4]] += Decimal(row["total_sale"])
            for row in result["annual"]:
                self.assertEqual(Decimal(str(row["revenue"])), totals[row["year"]])
            self.assertAlmostEqual(sum(r["revenue_change"] for r in result["category_growth_bridge"]), 6070)


if __name__ == "__main__": unittest.main()
