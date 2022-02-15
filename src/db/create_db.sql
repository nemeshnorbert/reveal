CREATE TABLE IF NOT EXISTS usd_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date VARCHAR(10) NOT NULL,
    symbol VARCHAR(6) NOT NULL,
    rate REAL NOT NULL,
    UNIQUE(date, symbol)
);

CREATE INDEX IF NOT EXISTS usd_rates_index
ON usd_rates(date, symbol);
