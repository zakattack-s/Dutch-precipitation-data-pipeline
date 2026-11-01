"""Build docs/municipalities.geojson and docs/cities.json for the map.

Usage:
  python prepare_places.py <municipality boundaries file> [cities15000.txt]

- Municipality file: any format geopandas reads (GeoJSON, GPKG, shapefile), any CRS.
- cities15000.txt: GeoNames file (download.geonames.org/export/dump/cities15000.zip, unzipped).
  Optional; without it only the municipality dropdown is built.
"""
import json, os, sys
import geopandas as gpd
import pandas as pd
import shapely

os.makedirs("docs", exist_ok=True)
g = gpd.read_file(sys.argv[1])
if g.crs is None:
    raise SystemExit("The boundary file has no CRS set; check which one it uses.")
g = g.to_crs(28992)
g["geometry"] = g.geometry.simplify(100)                       # 100 m: keeps the file small
g = g.to_crs(4326)
g["geometry"] = shapely.set_precision(g.geometry.values, 0.0001)   # ~10 m, short coordinates

cols = ["statnaam", "gemeentenaam", "naam", "name", "NAME_2"]
name_col = next((c for c in cols if c in g.columns), None) or \
           next(c for c in g.columns if c != "geometry" and g[c].dtype == object)
print("Using name column:", name_col)
g = g[[name_col, "geometry"]].rename(columns={name_col: "name"})
g = g[~g.geometry.is_empty]
g.to_file("docs/municipalities.geojson", driver="GeoJSON")
print(len(g), "municipalities ->", round(os.path.getsize("docs/municipalities.geojson") / 1e6, 2), "MB")

if len(sys.argv) > 2:
    c = pd.read_csv(sys.argv[2], sep="\t", header=None, quoting=3, usecols=[1, 4, 5, 8], dtype=str)
    c = c[c[8] == "NL"].drop_duplicates(1)
    rows = [[n, round(float(la), 4), round(float(lo), 4)] for n, la, lo in zip(c[1], c[4], c[5])]
    with open("docs/cities.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(len(rows), "cities -> docs/cities.json")
