import os
import sqlite3
import requests
import pytz
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
from tradingview_screener import Query, Column

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Force Eastern Timezone
EASTERN = pytz.timezone('US/Eastern')

# Scheduler setup
app.config['SCHEDULER_TIMEZONE'] = 'US/Eastern'
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DATABASE = os.path.join('instance', 'stocks.db')

def init_db():
    """Sets up the database to track ALL seen stocks under $100."""
    if not os.path.exists('instance'):
        os.makedirs('instance')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS all_stocks 
                 (symbol TEXT PRIMARY KEY, last_seen_under_100 INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_all_us_stocks_under_100():
    """Uses TradingView screener to find all US stocks under $100 with decent volume."""
    try:
        query = (Query()
                 .select('name', 'close', 'change', 'change_abs')
                 .where(
                     Column('close') < 100,
                     Column('exchange').isin(['NASDAQ', 'NYSE']),
                     Column('type') == 'stock',
                     Column('volume') > 50000
                 )
                 .limit(1000)
                 .get_scanner_data())
        
        df = query[1]
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'ticker': row['ticker'].split(':')[-1],
                'name': row['name'],
                'price': row['close'],
                'change_pct': row['change'],
                'change_abs': row['change_abs']
            })
        return stocks
    except Exception as e:
        print(f"Error screening stocks: {e}")
        return []

@app.route('/api/stocks')
def api_stocks():
    stocks = get_all_us_stocks_under_100()
    return jsonify(stocks[:100])

@app.route('/')
def index():
    return render_template('stocks.html')

def send_to_discord(content):
    if DISCORD_WEBHOOK_URL:
        try:
            if len(content) > 1900:
                chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                for chunk in chunks:
                    requests.post(DISCORD_WEBHOOK_URL, json={"content": chunk})
            else:
                requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")

@scheduler.task('interval', id='market_scan_task', hours=1)
def scan_market():
    """Runs every hour. Batches alerts and formats them like the original version."""
    with app.app_context():
        now_est = datetime.now(EASTERN)
        print(f"[{now_est.strftime('%Y-%m-%d %H:%M:%S %Z')}] Running full US market scan...")
        
        current_under_100 = get_all_us_stocks_under_100()
        if not current_under_100:
            print("No stocks found or error occurred.")
            return

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        new_discoveries = []
        
        for stock in current_under_100:
            symbol = stock['ticker']
            c.execute("SELECT last_seen_under_100 FROM all_stocks WHERE symbol = ?", (symbol,))
            result = c.fetchone()
            
            if result is None:
                new_discoveries.append(stock)
                c.execute("INSERT INTO all_stocks (symbol, last_seen_under_100) VALUES (?, 1)", (symbol,))
            elif result[0] == 0:
                new_discoveries.append(stock)
                c.execute("UPDATE all_stocks SET last_seen_under_100 = 1 WHERE symbol = ?", (symbol,))

        current_symbols = [s['ticker'] for s in current_under_100]
        c.execute("UPDATE all_stocks SET last_seen_under_100 = 0 WHERE last_seen_under_100 = 1 AND symbol NOT IN ({})".format(
            ','.join(['?'] * len(current_symbols))), current_symbols)
        
        conn.commit()
        conn.close()

        # 1. New Discoveries ALERT
        if new_discoveries:
            for s in new_discoveries[:5]: # Send individual alerts for first 5 new ones to mimic "old" style
                msg = f"🚨 **STOCK ALERT!** 🚨\n@everyone\n{s['ticker']} has hit ${s['price']:.2f}! (Target: <$100.00). Check it out: test@example.com"
                send_to_discord(msg)

        # 2. Hourly Batch Update (Classic Style)
        # Showing a smaller, cleaner batch to mimic the card-like appearance
        status_msg = f"📊 **US STOCKS UNDER $100** 📊\n*Refreshed at {now_est.strftime('%H:%M %p')}*\n\n"
        for s in current_under_100[:10]: # Top 10 for a clean look
            status_msg += f"**{s['ticker']}**: ${s['price']:.2f} | Today: {s['change_pct']:+.2f}%\n"
        
        send_to_discord(status_msg)

if __name__ == '__main__':
    init_db()
    scan_market()
    app.run(debug=True, port=5001, use_reloader=False)
