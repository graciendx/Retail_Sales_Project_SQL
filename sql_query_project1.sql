-- Reviewed SQLite analytical queries.
-- Reproduce with: python scripts/run_analysis.py
-- The runner loads validated sales and raw_sales tables before executing queries.
-- Public audit output contains aggregate counts only.

WITH yearly AS (
    SELECT substr(sale_date, 1, 4) AS year, COUNT(*) AS transactions,
           SUM(quantity) AS units, SUM(revenue_cents) AS revenue_cents
    FROM sales GROUP BY 1
)
SELECT year, transactions, units, revenue_cents / 100.0 AS revenue,
       revenue_cents / (100.0 * transactions) AS average_transaction_value,
       1.0 * revenue_cents / LAG(revenue_cents) OVER (ORDER BY year) - 1 AS revenue_growth,
       1.0 * transactions / LAG(transactions) OVER (ORDER BY year) - 1 AS transaction_growth
FROM yearly ORDER BY year;


-- Exact symmetric decomposition: change in n*a = delta_n*mean_a + delta_a*mean_n.
-- It avoids assigning the interaction term arbitrarily to one driver.
WITH category_year AS (
    SELECT category, substr(sale_date, 1, 4) AS year, COUNT(*) AS transactions,
           SUM(revenue_cents) / 100.0 AS revenue,
           SUM(revenue_cents) / (100.0 * COUNT(*)) AS average_value
    FROM sales GROUP BY 1, 2
), paired AS (
    SELECT *, LAG(transactions) OVER w AS prior_transactions,
           LAG(revenue) OVER w AS prior_revenue,
           LAG(average_value) OVER w AS prior_average_value,
           LAG(year) OVER w AS prior_year
    FROM category_year
    WINDOW w AS (PARTITION BY category ORDER BY year)
)
SELECT category, prior_year, year, prior_transactions, transactions, prior_revenue,
       revenue, revenue - prior_revenue AS revenue_change,
       (transactions - prior_transactions) * (average_value + prior_average_value) / 2 AS volume_contribution,
       (average_value - prior_average_value) * (transactions + prior_transactions) / 2 AS ticket_value_contribution
FROM paired WHERE prior_year = CAST(CAST(year AS INTEGER) - 1 AS TEXT)
ORDER BY revenue_change DESC, category;


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


WITH monthly AS (
    SELECT substr(sale_date, 1, 7) AS month, COUNT(*) AS transactions,
           SUM(revenue_cents) / 100.0 AS revenue
    FROM sales GROUP BY 1
), ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY substr(month, 1, 4) ORDER BY revenue DESC) AS revenue_rank_in_year
    FROM monthly
)
SELECT *, revenue / transactions AS average_transaction_value FROM ranked ORDER BY month;


-- Publish aggregate quality counts only; do not export individual identities.
WITH profiles AS (
    SELECT COUNT(DISTINCT NULLIF(gender, '')) AS gender_values,
           COUNT(DISTINCT NULLIF(age, '')) AS age_values
    FROM raw_sales GROUP BY customer_id
)
SELECT COUNT(*) AS customer_ids,
       SUM(CASE WHEN gender_values > 1 THEN 1 ELSE 0 END) AS ids_with_conflicting_gender,
       SUM(CASE WHEN age_values > 1 OR gender_values > 1 THEN 1 ELSE 0 END) AS ids_with_conflicting_profiles
FROM profiles;
