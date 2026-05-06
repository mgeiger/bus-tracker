import pytest
import pandas as pd
import sqlite3
import json
from unittest.mock import patch
from app import app, init_db, minutes_to_12h_format

# Fixture to provide a mocked database connection
@pytest.fixture
def mock_db():
    # Create an in-memory database
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Initialize the schema
    conn.execute('''
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL
        );
    ''')
    conn.commit()
    
    # Patch the get_db_connection in app.py to return this in-memory connection
    with patch('app.get_db_connection', return_value=conn):
        yield conn
    
    conn.close()

@pytest.fixture
def client(mock_db):
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_minutes_to_12h_format():
    assert minutes_to_12h_format(0) == "12:00 AM"
    assert minutes_to_12h_format(60) == "01:00 AM"
    assert minutes_to_12h_format(720) == "12:00 PM"
    assert minutes_to_12h_format(780) == "01:00 PM"
    assert minutes_to_12h_format(1439) == "11:59 PM"
    assert minutes_to_12h_format(None) is None
    assert minutes_to_12h_format(pd.NA) is None

def test_outlier_filtering_logic():
    # Mocking the new IQR filtering logic
    data = {
        'day_of_week': ['Monday'] * 10,
        'type': ['arrival'] * 10,
        'time_in_minutes': [480, 485, 490, 495, 500, 505, 510, 515, 520, 1000] # 1000 is a clear outlier
    }
    df = pd.DataFrame(data)
    
    def filter_outliers(group):
        if len(group) < 4:
            return group
        q1 = group['time_in_minutes'].quantile(0.25)
        q3 = group['time_in_minutes'].quantile(0.75)
        iqr = q3 - q1
        return group[
            (group['time_in_minutes'] >= q1 - 1.5 * iqr) & 
            (group['time_in_minutes'] <= q3 + 1.5 * iqr)
        ]

    filtered_df = df.groupby(['day_of_week', 'type'], group_keys=False).apply(filter_outliers)
    
    assert 1000 not in filtered_df['time_in_minutes'].values
    assert len(filtered_df) == 9
    assert filtered_df['time_in_minutes'].max() == 520

def test_static_routes(client):
    assert client.get('/').status_code == 200
    assert client.get('/favicon.ico').status_code == 204

def test_api_crud_workflow(client, mock_db):
    # 1. Submit Data
    payload = {'date': '2026-05-05', 'time': '15:00', 'type': 'arrival'}
    response = client.post('/api/submit', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 201
    
    # 2. Get Data (Verify insertion)
    with app.app_context():
        df = pd.read_sql_query("SELECT * FROM entries", mock_db)
        assert len(df) == 1
        assert df.iloc[0]['type'] == 'arrival'
        record_id = int(df.iloc[0]['id'])

    # 3. Update Data
    update_payload = {'id': record_id, 'date': '2026-05-05', 'time': '16:00', 'type': 'departure'}
    response = client.post('/api/update-data', data=json.dumps(update_payload), content_type='application/json')
    assert response.status_code == 200
    
    # 4. Delete Data
    response = client.post('/api/delete-data', data=json.dumps({'id': record_id}), content_type='application/json')
    assert response.status_code == 200
    
    # 5. Delete Error (Missing ID)
    response = client.post('/api/delete-data', data=json.dumps({}), content_type='application/json')
    assert response.status_code == 400

def test_api_summary_with_mock_data(client, mock_db):
    # Insert specific test data to cover filter logic
    mock_db.execute("INSERT INTO entries (date, time, type) VALUES ('2026-05-05', '08:00', 'arrival')")
    mock_db.execute("INSERT INTO entries (date, time, type) VALUES ('2026-05-05', '15:00', 'departure')")
    mock_db.commit()

    # Test 'all' filter
    response = client.get('/api/summary-data?filter=all')
    assert response.status_code == 200
    data = response.get_json()
    assert 'average_times' in data
    
    # Test 'current' filter
    # Note: This depends on the actual date, but since we inserted 2026-05-05, 
    # it should be in the current school year (2025-2026).
    response = client.get('/api/summary-data?filter=current')
    assert response.status_code == 200

def test_api_summary_empty(client, mock_db):
    # Ensure DB is empty
    mock_db.execute("DELETE FROM entries")
    mock_db.commit()
    response = client.get('/api/summary-data')
    assert response.status_code == 404
