# Bus Tracker Project

A web-based application for tracking and analyzing bus arrival and departure times.

## Project Overview

This project is a Flask application that allows users to record bus event data (arrivals and departures) and provides a visual summary of the data, including averages, minimum times, and distributions across different days of the week.

### Technologies
- **Backend:** Python 3.12, Flask
- **Data Analysis:** Pandas
- **Database:** SQLite
- **Frontend:** HTML/Jinja2, Bootstrap 5, Chart.js (with boxplot plugin)
- **Deployment:** Docker, Gunicorn

## Architecture

The application follows a simple monolithic architecture:
- `app.py`: Handles all routing, API endpoints, and database interactions.
- `database.db`: A local SQLite database. **Note:** This file is ignored by git (`.gitignore`) and is created/initialized on startup if it doesn't exist.
- `templates/`: Contains Jinja2 templates for the user interface.

### Data Management
- **Production Data:** The live `database.db` file is located on the `docker` host at `/home/mb/bus-tracker`.
- **Persistence:** In Docker environments, the database is persisted via a volume mount as defined in `docker-compose.yml`.

### Key API Endpoints
- `GET /api/raw-data`: Returns all entries in JSON format.
- `POST /api/submit`: Adds a new entry (date, time, type).
- `POST /api/update-data`: Updates an existing entry.
- `POST /api/delete-data`: Deletes an entry.
- `GET /api/summary-data`: Returns statistical summaries and chart data calculated via Pandas.

## Building and Running

### Local Development
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the application:**
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5000`.

### Docker
The application is containerized and can be run using Docker Compose.

1. **Build and run:**
   ```bash
   docker-compose up --build
   ```
   This uses Gunicorn to serve the application on port 5000.

## Development Conventions

- **Database:** The database schema is managed within `app.py` via `init_db()`.
- **Styling:** Bootstrap 5 is used for layout and components.
- **Charts:** Chart.js is used for data visualization.
- **Python Style:** Follow standard PEP 8 guidelines. The project uses `pandas` for data manipulation.
