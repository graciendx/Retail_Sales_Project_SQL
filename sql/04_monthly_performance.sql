WITH monthly AS (
    SELECT substr(sale_date, 1, 7) AS month, COUNT(*) AS transactions,
           SUM(revenue_cents) / 100.0 AS revenue
    FROM sales GROUP BY 1
), ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY substr(month, 1, 4) ORDER BY revenue DESC) AS revenue_rank_in_year
    FROM monthly
)
SELECT *, revenue / transactions AS average_transaction_value FROM ranked ORDER BY month;
