from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend to talk to backend

# In-memory storage for demonstration
donations = []

@app.route('/')
def home():
    return "FoodBridge Backend is Running!"

# Receive donation data
@app.route('/donate', methods=['POST'])
def donate():
    data = request.json
    if not data or "name" not in data or "food" not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    donations.append(data)
    return jsonify({"status": "success", "message": "Donation received!", "donations_count": len(donations)}), 200

# Get all donations
@app.route('/donations', methods=['GET'])
def get_donations():
    return jsonify(donations), 200

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- Initialize Database ---
conn = sqlite3.connect('foodbridge.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    food TEXT,
    quantity INTEGER,
    location TEXT,
    urgent INTEGER,
    priority INTEGER,
    status TEXT,
    created_at TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS donors(
    name TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0
)''')
conn.commit()

# --- Helper Functions ---
def calculate_priority(quantity, urgent):
    """Higher score = higher priority"""
    score = quantity
    if urgent:
        score += 5
    return score

# --- Routes ---

@app.route("/add", methods=["POST"])
def add_donation():
    data = request.json
    name = data.get("name") if not data.get("anonymous") else "Anonymous"
    food = data.get("food")
    quantity = data.get("quantity", 1)
    location = data.get("location")
    urgent = 1 if data.get("urgent") else 0
    created_at = datetime.now().isoformat()
    priority_score = calculate_priority(quantity, urgent)

    # Insert request
    c.execute('''INSERT INTO requests(name, food, quantity, location, urgent, priority, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, food, quantity, location, urgent, priority_score, "Pending", created_at))
    conn.commit()

    # Update donor points
    points_earned = quantity + (5 if urgent else 0)
    if name != "Anonymous":
        c.execute('SELECT points FROM donors WHERE name=?', (name,))
        row = c.fetchone()
        if row:
            new_points = row[0] + points_earned
            c.execute('UPDATE donors SET points=? WHERE name=?', (new_points, name))
        else:
            c.execute('INSERT INTO donors(name, points) VALUES (?, ?)', (name, points_earned))
        conn.commit()
        current_points = points_earned if not row else new_points
    else:
        current_points = 0

    return jsonify({"success": True, "points": current_points})

@app.route("/requests", methods=["GET"])
def get_requests():
    c.execute('SELECT * FROM requests ORDER BY priority DESC, created_at ASC')
    rows = c.fetchall()
    requests_list = []
    for r in rows:
        requests_list.append({
            "id": r[0],
            "name": r[1],
            "food": r[2],
            "quantity": r[3],
            "location": r[4],
            "urgent": bool(r[5]),
            "priority": "High" if r[6] >= 5 else "Medium",
            "status": r[7],
            "created_at": r[8]
        })
    return jsonify(requests_list)

@app.route("/accept", methods=["POST"])
def accept():
    id = request.json.get("id")
    c.execute('UPDATE requests SET status="Accepted" WHERE id=?', (id,))
    conn.commit()
    return jsonify({"success": True})

@app.route("/deliver", methods=["POST"])
def deliver():
    id = request.json.get("id")
    c.execute('UPDATE requests SET status="Delivered" WHERE id=?', (id,))
    conn.commit()
    return jsonify({"success": True})

@app.route("/points/<name>", methods=["GET"])
def get_points(name):
    c.execute('SELECT points FROM donors WHERE name=?', (name,))
    row = c.fetchone()
    if row:
        return jsonify({"points": row[0]})
    return jsonify({"points": 0})

# --- Run Server ---
if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)
conn = sqlite3.connect('foodbridge.db', check_same_thread=False)
c = conn.cursor()

# Create table if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    food TEXT,
    quantity INTEGER,
    location TEXT,
    urgent INTEGER,
    priority INTEGER,
    status TEXT,
    created_at TEXT
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS donors(
    name TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0
)
''')
conn.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    name = data.get("name") if not data.get("anonymous") else "Anonymous"
    food = data.get("food")
    quantity = data.get("quantity", 1)
    location = data.get("location")
    urgent = 1 if data.get("urgent") else 0
    created_at = datetime.now().isoformat()
    priority = quantity + (5 if urgent else 0)

    # Add request
    c.execute('''INSERT INTO requests(name, food, quantity, location, urgent, priority, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, food, quantity, location, urgent, priority, "Pending", created_at))
    conn.commit()

    # Update donor points
    points_earned = quantity + (5 if urgent else 0)
    if name != "Anonymous":
        c.execute('SELECT points FROM donors WHERE name=?', (name,))
        row = c.fetchone()
        if row:
            new_points = row[0] + points_earned
            c.execute('UPDATE donors SET points=? WHERE name=?', (new_points, name))
        else:
            c.execute('INSERT INTO donors(name, points) VALUES (?, ?)', (name, points_earned))
        conn.commit()

    return jsonify({"success": True, "points": points_earned})
@app.route('/requests', methods=['GET'])
def get_requests():
    c.execute('SELECT * FROM requests ORDER BY priority DESC, created_at ASC')
    rows = c.fetchall()
    requests_list = []
    for r in rows:
        requests_list.append({
            "id": r[0],
            "name": r[1],
            "food": r[2],
            "quantity": r[3],
            "location": r[4],
            "urgent": bool(r[5]),
            "priority": "High" if r[6] >= 5 else "Medium",
            "status": r[7],
            "created_at": r[8]
        })
    return jsonify(requests_list)
@app.route('/accept', methods=['POST'])
def accept():
    id = request.json.get("id")
    c.execute('UPDATE requests SET status="Accepted" WHERE id=?', (id,))
    conn.commit()
    return jsonify({"success": True})

@app.route('/deliver', methods=['POST'])
def deliver():
    id = request.json.get("id")
    c.execute('UPDATE requests SET status="Delivered" WHERE id=?', (id,))
    conn.commit()
    return jsonify({"success": True})
@app.route('/points/<name>', methods=['GET'])
def get_points(name):
    c.execute('SELECT points FROM donors WHERE name=?', (name,))
    row = c.fetchone()
    if row:
        return jsonify({"points": row[0]})
    return jsonify({"points": 0})
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
CORS(app)

# --- Database Setup ---
conn = sqlite3.connect('foodbridge.db', check_same_thread=False)
c = conn.cursor()

# Requests Table
c.execute('''
CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    food TEXT,
    quantity INTEGER,
    location TEXT,
    urgent INTEGER,
    priority INTEGER,
    status TEXT,
    created_at TEXT
)
''')

# Donors Table
c.execute('''
CREATE TABLE IF NOT EXISTS donors(
    name TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0
)
''')

# NGO Daily Pickup Tracker
c.execute('''
CREATE TABLE IF NOT EXISTS ngo_pickups(
    ngo_name TEXT,
    pickup_date TEXT,
    count INTEGER,
    PRIMARY KEY (ngo_name, pickup_date)
)
''')
conn.commit()

# --- Helper Functions ---
def calculate_priority(quantity, urgent):
    """Higher score = higher priority"""
    score = quantity
    if urgent:
        score += 5
    return score

def check_daily_limit(ngo_name, limit=5):
    today = date.today().isoformat()
    c.execute("SELECT count FROM ngo_pickups WHERE ngo_name=? AND pickup_date=?", (ngo_name, today))
    row = c.fetchone()
    if row:
        return row[0] < limit
    return True

def increment_daily_pickup(ngo_name):
    today = date.today().isoformat()
    c.execute("SELECT count FROM ngo_pickups WHERE ngo_name=? AND pickup_date=?", (ngo_name, today))
    row = c.fetchone()
    if row:
        c.execute("UPDATE ngo_pickups SET count=? WHERE ngo_name=? AND pickup_date=?", (row[0]+1, ngo_name, today))
    else:
        c.execute("INSERT INTO ngo_pickups(ngo_name, pickup_date, count) VALUES (?, ?, ?)", (ngo_name, today, 1))
    conn.commit()

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')  # Landing page

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')  # NGO Dashboard

@app.route('/add', methods=['POST'])
def add_donation():
    data = request.json
    name = data.get("name") if not data.get("anonymous") else "Anonymous"
    food = data.get("food")
    quantity = int(data.get("quantity", 1))
    location = data.get("location")
    urgent = 1 if data.get("urgent") else 0
    created_at = datetime.now().isoformat()
    priority_score = calculate_priority(quantity, urgent)

    # Insert request
    c.execute('''INSERT INTO requests(name, food, quantity, location, urgent, priority, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, food, quantity, location, urgent, priority_score, "Pending", created_at))
    conn.commit()

    # Update donor points
    points_earned = quantity + (5 if urgent else 0)
    if name != "Anonymous":
        c.execute('SELECT points FROM donors WHERE name=?', (name,))
        row = c.fetchone()
        if row:
            new_points = row[0] + points_earned
            c.execute('UPDATE donors SET points=? WHERE name=?', (new_points, name))
        else:
            c.execute('INSERT INTO donors(name, points) VALUES (?, ?)', (name, points_earned))
        conn.commit()
        current_points = points_earned if not row else new_points
    else:
        current_points = 0

    return jsonify({"success": True, "points": current_points})

@app.route('/requests', methods=['GET'])
def get_requests():
    # Order by priority descending, created_at ascending
    c.execute('SELECT * FROM requests ORDER BY priority DESC, created_at ASC')
    rows = c.fetchall()
    requests_list = []
    for r in rows:
        requests_list.append({
            "id": r[0],
            "name": r[1],
            "food": r[2],
            "quantity": r[3],
            "location": r[4],
            "urgent": bool(r[5]),
            "priority": "High" if r[6] >= 5 else "Medium",
            "status": r[7],
            "created_at": r[8]
        })
    return jsonify(requests_list)

@app.route('/accept', methods=['POST'])
def accept_request():
    id = request.json.get("id")
    ngo_name = request.json.get("ngo_name", "NGO")  # default NGO
    # Check daily limit
    if not check_daily_limit(ngo_name):
        return jsonify({"success": False, "message": "Daily pickup limit reached"}), 403

    c.execute('UPDATE requests SET status="Accepted" WHERE id=?', (id,))
    increment_daily_pickup(ngo_name)
    conn.commit()
    return jsonify({"success": True})

@app.route('/deliver', methods=['POST'])
def deliver_request():
    id = request.json.get("id")
    c.execute('UPDATE requests SET status="Delivered" WHERE id=?', (id,))
    conn.commit()
    return jsonify({"success": True})

@app.route('/points/<name>', methods=['GET'])
def get_points(name):
    c.execute('SELECT points FROM donors WHERE name=?', (name,))
    row = c.fetchone()
    if row:
        return jsonify({"points": row[0]})
    return jsonify({"points": 0})

# --- Run Server ---
if __name__ == "__main__":
    app.run(debug=True)
def advanced_priority(quantity, urgent, repeat_count, distance_km):
    """
    - urgent: 1 if urgent, 0 otherwise
    - repeat_count: number of times this beneficiary requested recently
    - distance_km: distance from donor
    """
    base = quantity
    base += urgent * 5
    base += repeat_count * 3  # repeated need adds priority
    base -= int(distance_km)  # farther requests get slightly lower priority
    return max(base, 0)