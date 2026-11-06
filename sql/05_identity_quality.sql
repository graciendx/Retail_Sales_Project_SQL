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
