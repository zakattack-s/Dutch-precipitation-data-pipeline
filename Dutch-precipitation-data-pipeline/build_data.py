"""Read nl_rain_ifs.parquet and export compact files for the web map."""
import json, os, shutil
import numpy as np
import pandas as pd

raw = pd.read_parquet("nl_rain_ifs.parquet")          # columns: date, cell_id, rain_mm
raw["date"] = pd.to_datetime(raw["date"])
raw["cell_id"] = raw["cell_id"].astype(int)
raw = raw.drop_duplicates(["date", "cell_id"]).sort_values(["date", "cell_id"])
print(len(raw), "rows,", raw.cell_id.nunique(), "cells,",
      raw.date.min().date(), "->", raw.date.max().date())

# days x cells table; missing days or cells become -1 (shown gray on the map)
wide = raw.pivot(index="date", columns="cell_id", values="rain_mm")
wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max()))
tenths = np.rint(wide * 10).fillna(-1).astype(int)    # rain in 0.1 mm integers

os.makedirs("docs", exist_ok=True)
out = {
    "dates": [d.strftime("%Y-%m-%d") for d in tenths.index],
    "ids": [int(c) for c in tenths.columns],
    "v": tenths.T.values.tolist(),                    # v[cell][day]
}
with open("docs/data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))
shutil.copy("ifs_cell_polygons.geojson", "docs/cells.geojson")
print("docs/data.json:", round(os.path.getsize("docs/data.json") / 1e6, 1), "MB")