import pytest
import pandas as pd
import sqlite3
import json
import os
from unittest.mock import patch
from app import app, minutes_to_12h_format

# Mock the PIN for tests
TEST_PIN = "123456"

@pytest.fixture(autouse=True)
def mock_env_pin():
    with patch.dict(os.environ, {"ENTRY_PIN": TEST_PIN}):
        with patch('app.ENTRY_PIN', TEST_PIN):
            yield

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

def test_static_routes(client):
    assert client.get('/').status_code == 200
    assert client.get('/favicon.ico').status_code == 204

def test_api_config(client):
    response = client.get('/api/config')
    assert response.status_code == 200
    assert response.get_json()['pin_required'] is True

def test_api_verify_pin(client):
    # Valid PIN
    response = client.post('/api/verify-pin', data=json.dumps({'pin': TEST_PIN}), content_type='application/json')
    assert response.status_code == 200
    # Invalid PIN
    response = client.post('/api/verify-pin', data=json.dumps({'pin': 'wrong'}), content_type='application/json')
    assert response.status_code == 401

def test_api_crud_workflow(client, mock_db):
    # 1. Submit Data (Fail with wrong PIN)
    payload = {'date': '2026-05-05', 'time': '15:00', 'type': 'arrival', 'pin': 'wrong'}
    response = client.post('/api/submit', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 401

    # 2. Submit Data (Success)
    payload['pin'] = TEST_PIN
    response = client.post('/api/submit', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 201
    
    # 3. Get Entries
    response = client.get('/api/entries')
    assert response.status_code == 200
    entries = response.get_json()
    assert len(entries) == 1
    record_id = entries[0]['id']

    # 4. Update Data (Fail with wrong PIN)
    update_payload = {'id': record_id, 'date': '2026-05-05', 'time': '16:00', 'type': 'departure', 'pin': 'wrong'}
    response = client.post('/api/update-data', data=json.dumps(update_payload), content_type='application/json')
    assert response.status_code == 401

    # 5. Update Data (Success)
    update_payload['pin'] = TEST_PIN
    response = client.post('/api/update-data', data=json.dumps(update_payload), content_type='application/json')
    assert response.status_code == 200
    
    # 6. Delete Data (Fail with no ID)
    response = client.post('/api/delete-data', data=json.dumps({'pin': TEST_PIN}), content_type='application/json')
    assert response.status_code == 400

    # 7. Delete Data (Fail with wrong PIN)
    response = client.post('/api/delete-data', data=json.dumps({'id': record_id, 'pin': 'wrong'}), content_type='application/json')
    assert response.status_code == 401

    # 8. Delete Data (Success)
    response = client.post('/api/delete-data', data=json.dumps({'id': record_id, 'pin': TEST_PIN}), content_type='application/json')
    assert response.status_code == 200

    # 9. Delete Data (Not Found)
    response = client.post('/api/delete-data', data=json.dumps({'id': 9999, 'pin': TEST_PIN}), content_type='application/json')
    assert response.status_code == 404

def test_api_summary_filtering(client, mock_db):
    # Setup: Add data inside and outside current school year
    mock_db.execute("INSERT INTO entries (date, time, type) VALUES ('2026-05-05', '08:00', 'arrival')")
    mock_db.execute("INSERT INTO entries (date, time, type) VALUES ('2020-05-05', '08:00', 'arrival')")
    mock_db.commit()

    # All filter
    response = client.get('/api/summary-data?filter=all')
    assert response.status_code == 200
    
    # Current filter (should exclude 2020)
    response = client.get('/api/summary-data?filter=current')
    assert response.status_code == 200

def test_api_summary_no_valid_data_after_outliers(client, mock_db):
    # Add only extreme outliers (e.g., 2 AM)
    mock_db.execute("INSERT INTO entries (date, time, type) VALUES ('2026-05-05', '02:00', 'arrival')")
    mock_db.commit()
    response = client.get('/api/summary-data?filter=all')
    assert response.status_code == 404
    assert "outlier filtering" in response.get_json()['message']

def test_api_summary_empty(client, mock_db):
    response = client.get('/api/summary-data')
    assert response.status_code == 404
