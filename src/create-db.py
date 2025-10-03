import sqlite3 as sl

con = sl.connect('exit_strategy.db')
with con:
    con.execute("""
        CREATE TABLE thresholds (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price INTEGER,
            amount INTEGER,
            threshold_hit STRING,
            sold_at REAL
        );
    """)

    con.execute("""
        CREATE TABLE hopper (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            amount INTEGER
        );
    """)

    con.execute("""
        CREATE TABLE available_funds (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            account_balance INTEGER,
            coin_hopper INTEGER
        );
    """)

    con.execute("""
        CREATE TABLE stoploss (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            stop_value REAL
        );
    """)

    con.execute("""
        CREATE TABLE win_tracker (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price_at_deposit REAL,
            price_at_buy INTEGER,
            buy_count INTEGER,
            win_count INTEGER
        );
    """)

    con.execute("""
        CREATE TABLE instance_locks (
            symbol TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            running INTEGER NOT NULL DEFAULT 0,
            pid INTEGER,
            started_at TEXT,
            updated_at TEXT,
            PRIMARY KEY (symbol, trade_type)
        );
    """)  

# Note: No default data inserted
# Each instance will insert its own data per symbol when started
# Database is now ready for multi-instance usage

print("Database created successfully!")
print("Tables: thresholds, hopper, available_funds, stoploss, win_tracker, instance_locks")
print("All tables include 'symbol' column for multi-instance support")