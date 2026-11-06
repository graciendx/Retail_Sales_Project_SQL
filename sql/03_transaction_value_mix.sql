-- 1,000 source currency units is an illustrative fixed threshold, not a premium label.
WITH bands AS (
    SELECT substr(sale_date, 1, 4) AS year,
           CASE WHEN revenue_cents >= 100000 THEN 'At least 1000' ELSE 'Below 1000' END AS value_band,
           COUNT(*) AS transactions, SUM(revenue_cents) / 100.0 AS revenue
    FROM sales GROUP BY 1, 2
)
SELECT *, revenue / SUM(revenue) OVER (PARTITION BY year) AS year_revenue_share,
       1.0 * transactions / SUM(transactions) OVER (PARTITION BY year) AS year_transaction_share
FROM bands ORDER BY year, value_band;
