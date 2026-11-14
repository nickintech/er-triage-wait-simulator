"""Run with python3 app.py, then open http://127.0.0.1:8000."""
from heapq import heapify, heapreplace
from http.server import BaseHTTPRequestHandler, HTTPServer
from random import Random
import sqlite3
from urllib.parse import parse_qs, urlsplit


PEAK_MINUTES = 240


def make_arrivals(per_hour):
    """Generate one synthetic arrival and service schedule for both scenarios."""
    rng = Random(17)
    minute = rng.expovariate(per_hour / 60)
    arrivals = []
    while minute < PEAK_MINUTES:
        arrivals.append((minute, rng.randint(6, 14)))
        minute += rng.expovariate(per_hour / 60)
    return arrivals


def simulate(arrivals, nurses):
    available = [0] * nurses
    heapify(available)
    for arrival, service in arrivals:
        start = max(arrival, available[0])
        heapreplace(available, start + service)
        yield (nurses, arrival, start)


def compare(per_hour):
    arrivals = make_arrivals(per_hour)
    if not arrivals:
        return [(nurses, 0, None, None, 0) for nurses in (2, 3)]
    database = sqlite3.connect(":memory:")
    try:
        database.execute("CREATE TABLE visits (nurses INTEGER, arrival REAL, start REAL)")
        for nurses in (2, 3):
            database.executemany("INSERT INTO visits VALUES (?, ?, ?)", simulate(arrivals, nurses))
        return database.execute(
            """
            SELECT nurses, COUNT(*), AVG(start - arrival), MAX(start - arrival),
                   SUM(CASE WHEN start > ? THEN 1 ELSE 0 END)
            FROM visits GROUP BY nurses ORDER BY nurses
            """,
            (PEAK_MINUTES,),
        ).fetchall()
    finally:
        database.close()


def page(per_hour):
    results = compare(per_hour)
    cards = []
    for nurses, count, average, maximum, waiting in results:
        average_label = "—" if average is None else f"{average:.1f} min"
        maximum_label = "—" if maximum is None else f"{maximum:.1f} min"
        cards.append(f"""
          <section>
            <h2>{nurses} triage nurses</h2>
            <strong>{average_label}</strong>
            <p>Average wait to start triage</p>
            <dl><dt>Longest wait</dt><dd>{maximum_label}</dd>
            <dt>Still waiting after 4 hours</dt><dd>{waiting} of {count}</dd></dl>
          </section>""")
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ER triage wait simulator</title>
<style>
  * {{box-sizing:border-box}}
  body {{background:#eff5f4;color:#153731;font:17px/1.55 system-ui,sans-serif;margin:0}}
  main {{max-width:880px;margin:auto;padding:clamp(20px,6vw,60px)}}
  h1 {{font-size:clamp(2rem,6vw,3.5rem);line-height:1.05;margin:.35em 0}}
  form,.cards {{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}
  form {{align-items:end}}
  label {{display:grid;gap:6px}}
  input,button {{font:inherit;padding:9px 14px;border-radius:8px;border:1px solid #52716b}}
  input {{width:100px}}
  button {{background:#165648;color:white;cursor:pointer}}
  section {{flex:1 1 250px;background:white;border:1px solid #c7dbd7;border-radius:16px;padding:22px}}
  h2 {{font-size:1.15rem;margin:0 0 12px}}
  strong {{font-size:2.4rem;line-height:1;color:#165648}}
  p {{margin:.6em 0}}
  dl {{display:grid;grid-template-columns:1fr auto;gap:8px;margin:20px 0 0}}
  dd {{margin:0;font-weight:650}}
  small {{display:block;color:#355950}}
</style>
<main>
  <h1>ER triage wait simulator</h1>
  <p>Compare two and three triage nurses during a four-hour arrival window.</p>
  <form action="/">
    <label for="rate">Expected arrivals per hour
      <input id="rate" name="rate" type="number" value="{per_hour}" min="1" max="60" required>
    </label>
    <button>Run simulation</button>
  </form>
  <div class="cards">{''.join(cards)}</div>
  <small>Simulated data. Both scenarios use the same arrivals and triage times. The queue starts
  empty and serves patients in arrival order. Triage continues after the four-hour window so
  waits can be measured for every arrival. The simulation omits patient acuity, staffing breaks,
  and treatment after triage. For portfolio demonstration only.</small>
</main>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != "/":
            self.send_error(404)
            return
        try:
            rate = int(parse_qs(url.query, keep_blank_values=True).get("rate", ["16"])[0])
            if not 1 <= rate <= 60:
                raise ValueError
        except ValueError:
            self.send_error(400, "Enter a whole number from 1 to 60.")
            return

        body = page(rate).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
