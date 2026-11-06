CREATE TABLE raw_sales (
    transactions_id TEXT, sale_date TEXT, sale_time TEXT, customer_id TEXT,
    gender TEXT, age TEXT, category TEXT, quantiy TEXT, price_per_unit TEXT,
    cogs TEXT, total_sale TEXT, revenue_eligible INTEGER NOT NULL,
    exclusion_reason TEXT NOT NULL
);

-- Money is stored as integer hundredths of the source's unspecified currency.
CREATE TABLE sales (
    transaction_id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL,
    sale_time TEXT NOT NULL, customer_id TEXT NOT NULL, category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price_cents INTEGER NOT NULL,
    revenue_cents INTEGER NOT NULL,
    CHECK(revenue_cents = quantity * unit_price_cents)
);
