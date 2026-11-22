# X (Twitter) Topic Tracker

Automated Python pipeline that collects, filters, and deduplicates posts from X on specific keywords using twifork.

## Setup
1. Create a virtual environment and install dependencies:
   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
2. Copy cookies.example.json to cookies.json and add your session tokens.
3. Run manually with python scraper.py --now or schedule via macOS launchd.


### Use at 