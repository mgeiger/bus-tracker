from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                type TEXT NOT NULL
            );
        ''')
        conn.commit()

# Initialize the database when the app starts
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary')
def summary():
    return render_template('summary.html')

@app.route('/raw-data')
def raw_data_page():
    return render_template('raw-data.html')

@app.route('/api/submit', methods=['POST'])
def submit_data():
    data = request.get_json()
    date = data['date']
    time = data['time']
    entry_type = data['type']

    with get_db_connection() as conn:
        conn.execute('INSERT INTO entries (date, time, type) VALUES (?, ?, ?)',
                     (date, time, entry_type))
        conn.commit()
    return jsonify({"message": "Data submitted successfully!"}), 201

@app.route('/api/update-data', methods=['POST'])
def update_data():
    data = request.get_json()
    record_id = data['id']
    new_date = data['date']
    new_time = data['time']
    new_type = data['type']

    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE entries SET date = ?, time = ?, type = ? WHERE id = ?",
                (new_date, new_time, new_type, record_id)
            )
            conn.commit()
        return jsonify({"message": "Record updated successfully!"}), 200
    except sqlite3.Error as e:
        return jsonify({"message": f"Error updating record: {e}"}), 500
    
@app.route('/api/delete-data', methods=['POST'])
def delete_data():
    data = request.get_json()
    record_id = data.get('id')

    if not record_id:
        return jsonify({"message": "ID is required to delete a record."}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entries WHERE id = ?", (record_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"message": "Record not found."}), 404
        return jsonify({"message": "Record deleted successfully!"}), 200
    except sqlite3.Error as e:
        return jsonify({"message": f"Error deleting record: {e}"}), 500

@app.route('/api/raw-data')
def get_raw_data():
    with get_db_connection() as conn:
        data = conn.execute("SELECT id, date, time, type FROM entries ORDER BY date DESC, time DESC").fetchall()

    raw_data = [dict(row) for row in data]
    return jsonify(raw_data)


from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                type TEXT NOT NULL
            );
        ''')
        conn.commit()

# Initialize the database when the app starts
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary')
def summary():
    return render_template('summary.html')

@app.route('/raw-data')
def raw_data_page():
    return render_template('raw-data.html')

@app.route('/api/submit', methods=['POST'])
def submit_data():
    data = request.get_json()
    date = data['date']
    time = data['time']
    entry_type = data['type']

    with get_db_connection() as conn:
        conn.execute('INSERT INTO entries (date, time, type) VALUES (?, ?, ?)',
                     (date, time, entry_type))
        conn.commit()
    return jsonify({"message": "Data submitted successfully!"}), 201

@app.route('/api/update-data', methods=['POST'])
def update_data():
    data = request.get_json()
    record_id = data['id']
    new_date = data['date']
    new_time = data['time']
    new_type = data['type']

    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE entries SET date = ?, time = ?, type = ? WHERE id = ?",
                (new_date, new_time, new_type, record_id)
            )
            conn.commit()
        return jsonify({"message": "Record updated successfully!"}), 200
    except sqlite3.Error as e:
        return jsonify({"message": f"Error updating record: {e}"}), 500

@app.route('/api/delete-data', methods=['POST'])
def delete_data():
    data = request.get_json()
    record_id = data.get('id')

    if not record_id:
        return jsonify({"message": "ID is required to delete a record."}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entries WHERE id = ?", (record_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"message": "Record not found."}), 404
        return jsonify({"message": "Record deleted successfully!"}), 200
    except sqlite3.Error as e:
        return jsonify({"message": f"Error deleting record: {e}"}), 500

@app.route('/api/raw-data')
def get_raw_data():
    with get_db_connection() as conn:
        data = conn.execute("SELECT id, date, time, type FROM entries ORDER BY date DESC, time DESC").fetchall()
    
    raw_data = [dict(row) for row in data]
    return jsonify(raw_data)

@app.route('/api/summary-data')
def get_summary_data():
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM entries", conn)

    if df.empty:
        return jsonify({"message": "No data available."}), 404

    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df['day_of_week'] = df['datetime'].dt.day_name()
    df['time_in_minutes'] = df['datetime'].dt.hour * 60 + df['datetime'].dt.minute

    # Calculate both average and minimum times
    stats_df = df.groupby(['day_of_week', 'type'])['time_in_minutes'].agg(['mean', 'min']).reset_index()

    average_times_dict = {}
    min_times_dict = {}

    for _, row in stats_df.iterrows():
        day = row['day_of_week']
        entry_type = row['type']
        
        avg_minutes = row['mean']
        avg_time_str = f"{int(avg_minutes // 60):02d}:{int(avg_minutes % 60):02d}"
        
        min_minutes = row['min']
        min_time_str = f"{int(min_minutes // 60):02d}:{int(min_minutes % 60):02d}"
        
        if day not in average_times_dict:
            average_times_dict[day] = {}
            min_times_dict[day] = {}
        
        average_times_dict[day][entry_type] = avg_time_str
        min_times_dict[day][entry_type] = min_time_str

    # Prepare data for the line chart
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    arrival_times = [
        average_times_dict.get(day, {}).get('arrival', None)
        for day in day_order
    ]
    
    departure_times = [
        average_times_dict.get(day, {}).get('departure', None)
        for day in day_order
    ]
    
    return jsonify({
        'average_times': average_times_dict,
        'min_times': min_times_dict,
        'line_chart_data': {
            'labels': day_order,
            'datasets': [
                {
                    'label': 'Arrivals',
                    'data': [int(t[:2])*60 + int(t[3:]) if t else None for t in arrival_times],
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'tension': 0.1,
                },
                {
                    'label': 'Departures',
                    'data': [int(t[:2])*60 + int(t[3:]) if t else None for t in departure_times],
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'tension': 0.1,
                }
            ]
        }
    })

if __name__ == '__main__':
    app.run(debug=True)





if __name__ == '__main__':
    app.run(debug=True)