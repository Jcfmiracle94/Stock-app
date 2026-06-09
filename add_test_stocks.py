import sqlite3
import os

DATABASE = os.path.join('instance', 'stocks.db')

def add_penny_stocks():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Add some stocks that are definitely under $100
    new_stocks = [
        ('F', 100.0, 'test@example.com', 0),    # Ford
        ('PFE', 100.0, 'test@example.com', 0),  # Pfizer
        ('SNAP', 100.0, 'test@example.com', 0)  # Snap
    ]
    for stock in new_stocks:
        try:
            c.execute("INSERT INTO stocks (symbol, target_price, email, last_seen_under_100) VALUES (?, ?, ?, ?)", stock)
        except sqlite3.IntegrityError:
            # Already exists, just make sure it's reset to 0 to trigger the @everyone alert
            c.execute("UPDATE stocks SET last_seen_under_100 = 0 WHERE symbol = ?", (stock[0],))
    
    conn.commit()
    print("Added/Reset Ford (F), Pfizer (PFE), and Snap (SNAP) for testing.")
    conn.close()

if __name__ == '__main__':
    add_penny_stocks()
