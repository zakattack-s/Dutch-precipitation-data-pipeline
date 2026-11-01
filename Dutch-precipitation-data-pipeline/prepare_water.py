"""Build docs/water.geojson: the main lakes and rivers of the Netherlands, from Natural Earth (public domain).

Usage:  python prepare_water.py
Needs internet and shapely. The IJsselmeer polygon in this dataset includes the Markermeer.
"""
import json, os, urllib.request
import shapely
from shapely.geometry import box, mapping, shape

BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
AREA = box(3.2, 50.7, 7.3, 53.6)                               # the Netherlands plus a margin
LAKES = {"IJsselmeer", "Lauwerszee", "Heegermeer en Fluessen", "Tjeukemeer"}
RIVERS = {"IJssel", "Nederrijn", "Lek", "Waal", "Maas", "Rhine", "Schelde", "Vecht"}

def load(name):
    with urllib.request.urlopen(BASE + name + ".geojson", timeout=120) as r:
        return json.load(r)["features"]

out = []
def add(f, kind, name):
    g = shape(f["geometry"]).intersection(AREA)
    if g.is_empty:
        return
    g = shapely.set_precision(g, 0.0001)                       # short coordinates, small file
    out.append({"type": "Feature", "properties": {"kind": kind, "name": name}, "geometry": mapping(g)})

for src in ("ne_10m_lakes", "ne_10m_lakes_europe"):
    for f in load(src):
        if f["properties"].get("name") in LAKES:
            add(f, "lake", f["properties"]["name"])
for src in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe"):
    for f in load(src):
        n = f["properties"].get("name")
        if n in RIVERS:
            add(f, "river", n)
        elif n is None and f["geometry"] and shape(f["geometry"]).intersects(box(4.5, 52.3, 5.0, 52.5)):
            add(f, "river", "Noordzeekanaal")                  # unnamed canal Amsterdam to IJmuiden

os.makedirs("docs", exist_ok=True)
with open("docs/water.geojson", "w") as fh:
    json.dump({"type": "FeatureCollection", "features": out}, fh, separators=(",", ":"))
print(len(out), "features ->", round(os.path.getsize("docs/water.geojson") / 1e3), "KB")
