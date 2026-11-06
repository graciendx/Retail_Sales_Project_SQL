# Retail Revenue Growth and Data Quality

**Grace Ngo | SQL analytical extension**

What explains the change in 2023 revenue: more transactions, larger purchases, or a different category mix? Can the same data support credible customer-retention analysis?

This project extends an introductory retail SQL exercise into a revenue diagnostic with a reconciled growth bridge, transaction-value concentration and an explicit customer-identity audit. It uses the repository's original 2,000-row teaching dataset; it does not claim access to a real retailer's operations or a measured commercial uplift.

## Findings

| Measure | 2022 | 2023 | Change |
| --- | ---: | ---: | ---: |
| Revenue, source currency units | 452,825 | 458,895 | +1.34% |
| Eligible transactions | 976 | 1,021 | +4.61% |
| Average transaction value | 463.96 | 449.46 | -3.13% |

The sample's revenue increase was modest despite higher transaction volume. Average transaction value fell, and category gains were partly offset by Beauty's decline.

| Category | Revenue change | Transaction-volume contribution | Transaction-value contribution |
| --- | ---: | ---: | ---: |
| Clothing | +11,360 | +15,541.74 | -4,181.74 |
| Electronics | +10,890 | +10,092.48 | +797.52 |
| Beauty | -16,180 | -5,620.25 | -10,559.75 |
| Total | **+6,070** | **+20,013.96** | **-13,943.96** |

The contributions use an exact symmetric volume/value decomposition. They reconcile to category and overall revenue changes. The value component can reflect purchase size, price and product mix; this dataset cannot separate all three.

Transactions worth at least 1,000 source currency units accounted for **20.3% of 2023 transactions and 63.8% of revenue**. This fixed, illustrative cutoff identifies revenue concentration. It does not establish that these purchases are premium products or profitable orders.

**A consequential data limitation:** 151 of 155 customer IDs map to more than one recorded gender value, and all 155 have conflicting age/gender profiles. These IDs are unsuitable for a defensible retention or demographic-targeting claim. Identifying that defect is more useful than publishing a customer segmentation that assumes identities are reliable.

## Business interpretation

The next investigation would focus on Beauty's lower purchase value and reduced transaction count, then determine whether Clothing's volume growth depends on discounting or lower-priced products. The source lacks SKU-level detail, promotions, returns and a reliable COGS definition, so these are follow-up questions rather than established causes. Before retention analysis, the customer identifier must be reconciled to a trusted master record.

## Reproduce

Python 3.11 or later, with its bundled SQLite. No third-party packages or database server are required.

```sh
git clone https://github.com/graciendx/Retail_Sales_Project_SQL.git
cd Retail_Sales_Project_SQL
python scripts/run_analysis.py
python -m unittest discover -s tests -v
```

To write results elsewhere: `python scripts/run_analysis.py --output /tmp/retail-analysis`.

The runner creates an in-memory SQLite database, retains all source rows in staging, loads eligible transactions, executes the SQL files and exports five result tables plus a [summary](reports/summary.json). It fails if the growth bridge does not reconcile. [GitHub Actions](.github/workflows/checks.yml) repeats the tests and full analysis.

## Data-quality policy

- **Preserve the input.** The original CSV is unchanged. Raw staging records include eligibility and exclusion reasons; no destructive `DELETE` cleaning is used.
- **Define eligibility by the question.** Three rows lack revenue inputs and are excluded from revenue metrics. Ten otherwise valid transactions with missing age are retained. Missing demographic data do not make a sale unusable.
- **Validate transactions.** Check keys, dates, times, positive quantities and exact agreement between quantity times unit price and recorded revenue. Duplicate transaction IDs stop the analysis.
- **Use exact monetary storage.** Values are stored as integer hundredths; the source does not identify a currency, so no dollar symbol is added.
- **Restrict unsupported outputs.** The COGS field has no documented unit basis. Profit and gross margin are not estimated. Inconsistent customer profiles preclude reliable retention and targeting analysis.

Of 2,000 source rows, **1,997 transactions** enter the revenue analysis. Every excluded row remains inspectable in staging. The monthly output reports observed sample sales; varying record density and two years of teaching data do not establish retailer-wide seasonality, store productivity or staffing requirements.

## SQL and repository structure

| File | Purpose |
| --- | --- |
| `sql/schema.sql` | Raw staging and validated transaction schema |
| `sql/01_annual_performance.sql` | Annual revenue, transaction volume and average value |
| `sql/02_category_growth_bridge.sql` | Window functions and reconciled volume/value decomposition |
| `sql/03_transaction_value_mix.sql` | Fixed-band revenue concentration and denominator-aware shares |
| `sql/04_monthly_performance.sql` | Monthly revenue and tied ranks within each year |
| `sql/05_identity_quality.sql` | Aggregate customer-profile consistency audit; no individual identifiers in the report |
| `scripts/run_analysis.py` | Validation, loading, execution and reproducible exports |
| `tests/test_analysis.py` | Seven tests, including independent source-total reconciliation |
| `reports/` | Generated tables and source fingerprint |

The canonical queries target **SQLite 3.25+** and are run by the Python entry point. The legacy `sql_query_project1.sql` now contains the same reviewed analytical queries for readers following the original filename. Earlier PostgreSQL-oriented classroom queries remain in Git history.

## Provenance and authorship

The existing dataset and introductory question format predate this extension. Their upstream creator, sampling method and license were not documented in the repository, so the dataset is described as teaching data and no new data-license claim is made. The publication adds the revenue question, metric-specific inclusion policy, SQL growth bridge, identity audit, executable loader, checks and findings. It does not describe the tutorial dataset as original data collection.

[Portfolio case study](https://graciendx.github.io/case-studies/retail-revenue.html) | [Grace Ngo's portfolio](https://graciendx.github.io/)
