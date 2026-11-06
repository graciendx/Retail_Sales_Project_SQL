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
