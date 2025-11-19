# Game Art Visualizer

This project fetches game data + screenshots from IGDB, extracts color palettes,
stores everything in a local SQLite database, and visualizes art trends.

## Setup

1. Create a virtual environment (recommended):
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Copy `.env.example` to `.env` and fill in your Twitch/IGDB credentials:
   CLIENT_ID=your_twitch_client_id
   CLIENT_SECRET=your_twitch_client_secret

4. Run the ETL process to populate the database:
   python -m src.etl_fetch

5. Start the dashboard:
   streamlit run app/dashboard.py
