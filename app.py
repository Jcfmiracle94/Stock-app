# ==============================================================================
# SECTION 1: IMPORTING TOOLS
# Think of these like "app extensions" that give our program extra powers.
# ==============================================================================
from flask import Flask, render_template, request, redirect, url_for
import sqlite3 # This tool lets us talk to a database (like a digital filing cabinet).
from datetime import datetime # This helps the computer understand dates and times.
import pytz # This is a massive list of all time zones in the world.

# ==============================================================================
# SECTION 2: SETTING UP THE APP
# This line creates the "brain" of our web application.
# ==============================================================================
app = Flask(__name__)

# ==============================================================================
# SECTION 3: THE DATABASE (THE FILING CABINET)
# This function sets up a place to store names people type in.
# ==============================================================================
def init_db():
    # 'sqlite3.connect' opens a file called 'users.db'. If it doesn't exist, it creates it.
    conn = sqlite3.connect('users.db')
    c = conn.cursor() # The 'cursor' is like a pen we use to write in the database.
    
    # This command tells the database: "Create a table called 'submissions' if you haven't already."
    # It will have columns for an ID, the user's Name, and the Time they signed in.
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, name TEXT, timestamp TEXT)''')
    
    conn.commit() # This "saves" our work.
    conn.close() # This "closes" the cabinet so we don't leave it messy.

# ==============================================================================
# SECTION 4: THE HOME PAGE ROUTE
# When you first go to the website (the '/' path), this function runs.
# ==============================================================================
@app.route('/')
def index():
    # This tells the computer: "Go find the file named index.html and show it to the user."
    return render_template('index.html')

# ==============================================================================
# SECTION 5: THE SUBMIT BUTTON LOGIC
# This runs when the user clicks 'Submit' on the home page.
# ==============================================================================
@app.route('/submit', methods=['POST'])
def submit():
    # It grabs the 'name' that the user typed into the box.
    name = request.form.get('name')
    
    if name:
        # We open our digital filing cabinet again...
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # ...and we "write" the name and the current time into it.
        c.execute("INSERT INTO submissions (name, timestamp) VALUES (?, ?)", (name, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    # After saving the name, we "redirect" (send) the user to the results page.
    return redirect(url_for('results'))

# ==============================================================================
# SECTION 6: THE RESULTS PAGE (TIME ZONES)
# This page shows the current time in every single time zone on Earth.
# ==============================================================================
@app.route('/results')
def results():
    # We get a list of every single time zone name from the 'pytz' tool.
    timezones = pytz.all_timezones
    times = [] # We create an empty list to hold the formatted times.
    
    # This 'for' loop goes through every time zone one by one.
    for tz_name in timezones:
        try:
            # We ask the computer: "What time is it right now in this specific zone?"
            tz = pytz.timezone(tz_name)
            tz_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            
            # We "append" (add) that zone and its time to our list.
            times.append({'zone': tz_name, 'time': tz_time})
        except Exception:
            # If a specific time zone has an error, we just skip it.
            continue
            
    # Finally, we send that big list of times to the 'results.html' file to display it.
    return render_template('results.html', times=times)

# ==============================================================================
# SECTION 7: STARTING THE ENGINE
# This is the "on switch" for the entire website.
# ==============================================================================
if __name__ == '__main__':
    init_db() # Run the database setup first.
    app.run(debug=True, port=5000) # Start the website so people can visit it.
