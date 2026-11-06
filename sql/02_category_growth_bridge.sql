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
