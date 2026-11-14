# ER Triage Wait Simulator

A Python and SQLite project that explores how staffing can affect
wait times in an emergency room. It compares two scenarios:
two triage nurses and three triage nurses.

## Data

The simulator uses fictional patient arrivals to model both scenarios.

## How to run

1. Download the project and open Terminal in the folder containing `app.py`.
2. Run:

   ```bash
   python3 app.py
   ```

3. Leave Terminal open and visit `http://127.0.0.1:8000` in your browser.
4. Enter a patient arrival rate to compare simulated waits for two and three triage nurses.

To stop the server, return to Terminal and press `Control+C`.
