import os, time, requests, pandas as pd
from datetime import date, timedelta

url = "https://archive-api.open-meteo.com/v1/archive"
rain_data = "nl_rain_ifs.parquet"                   # import all rain data

cells = pd.read_parquet("ifs_cells.parquet")      # import the cells coordinates
batch_size = 10
DELAY_DAYS = 5          # newest day requested = today - 5
OVERLAP_DAYS = 3        # re-fetch the last 3 saved days (catches revisions)

def fetch_cells(batch, start, end):
    params = {
        "latitude": ",".join(f"{x:.4f}" for x in batch["lat"]),
        "longitude": ",".join(f"{x:.4f}" for x in batch["lon"]),
        "start_date": start, "end_date": end,
        "daily": "precipitation_sum", "models": "ecmwf_ifs",
        "timezone": "Europe/Amsterdam",
    }
    for attempt in range(5):
        r = requests.get(url, params=params, timeout=120)
        if r.status_code == 429:
            reason = r.json().get("reason", "")
            print("Rate limited:", reason)
            if "daily" in reason.lower():
                return None                        # out of budget for today
            time.sleep(60)                         # minute/hour limit: wait, retry
            continue
        r.raise_for_status()
        data = r.json()
        return [data] if isinstance(data, dict) else data
    return None                                    # still limited: stop the run

def update():
    old = pd.read_parquet(rain_data)
    old["date"] = pd.to_datetime(old["date"])
    old["cell_id"] = old["cell_id"].astype(int)    
    if old["cell_id"].nunique() < len(cells):
        print(f"WARNING: file has {old['cell_id'].nunique()} cells, expected {len(cells)}")

    last = old.groupby("cell_id")["date"].max().min().date()   # newest day EVERY cell has
    end = date.today() - timedelta(days=DELAY_DAYS)
    if last >= end:
        print(f"Up to date (last date {last})")
        return
    start = last - timedelta(days=OVERLAP_DAYS - 1)
    print(f"Fetching {start} -> {end}")

    parts = []
    for b in range(0, len(cells), batch_size):
        batch = cells.iloc[b:b + batch_size]
        answers = fetch_cells(batch, start.isoformat(), end.isoformat())
        if answers is None:
            print("Stopping; nothing was saved. Run again later.")
            return
        for (_, c), loc in zip(batch.iterrows(), answers):
            if abs(loc["latitude"] - c.lat) > 0.001 or abs(loc["longitude"] - c.lon) > 0.001:
                print("WARNING: cell mismatch", int(c.cell_id))
            parts.append(pd.DataFrame({
                "date": pd.to_datetime(loc["daily"]["time"]),
                "rain_mm": loc["daily"]["precipitation_sum"],
                "cell_id": int(c.cell_id),
            }))
        time.sleep(2)                              # stay well under the per-minute limit

    new = pd.concat(parts, ignore_index=True).dropna(subset=["rain_mm"])
    if new.empty:
        print("No new data available yet.")
        return
    # keep only days where every cell has a value, so no permanent gaps
    new = new[new["date"] <= new.groupby("cell_id")["date"].max().min()]

    df = (pd.concat([old, new], ignore_index=True)
            .drop_duplicates(["date", "cell_id"], keep="last")   # overlap: new wins
            .sort_values(["date", "cell_id"]).reset_index(drop=True))
    df.to_parquet(rain_data + ".tmp")
    os.replace(rain_data + ".tmp", rain_data)          # write is all-or-nothing
    print(f"Saved. Last date: {df['date'].max().date()}, rows: {len(df)}")

if __name__ == "__main__":
    update()
