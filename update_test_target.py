import sqlite3
import os

DATABASE = os.path.join('instance', 'stocks.db')

def update_target():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE stocks SET target_price = 400.0 WHERE symbol = 'AAPL'")
    conn.commit()
    print(f"Updated AAPL target to $400.00. Rows affected: {c.rowcount}")
    conn.close()

if __name__ == '__main__':
    update_target()
