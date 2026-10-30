# Netherlands daily rain map

## Repository layout

```
ifs_cells.parquet            cell centres (from your discovery step)
ifs_cell_polygons.geojson    Voronoi polygons (from your polygon step)
ifs_raw/                     the 2xxx_000.parquet ... chunk files
update_ifs.py                your incremental updater (see step 1)
build_data.py                merges chunks, writes docs/data.json + docs/cells.geojson
docs/index.html              the map page
.github/workflows/update.yml scheduled update
.gitignore                   add the line:  nl_rain_ifs.parquet
```

## Steps

1. **Updater script.** Save your updater code as `update_ifs.py`. Replace the bare `run()` on the last line with:
   ```python
   if __name__ == "__main__":
       run()
   ```
2. **Test locally.** Run `python build_data.py`, then `cd docs` and `python -m http.server 8000`, and open http://localhost:8000. (Opening index.html by double-click will not work, because browsers block `fetch` on local files.)
3. **Create a GitHub repo** and push everything. Commit `ifs_raw/`, `ifs_cells.parquet`, `ifs_cell_polygons.geojson`, `docs/` and the workflow.
4. **Turn on Pages:** Settings, Pages, Source: *Deploy from a branch*, branch `main`, folder `/docs`.
5. **Run the workflow once by hand:** Actions tab, *Update rain data*, Run workflow. Check that it commits new data.

## Things to check

- If the site does not refresh after the workflow commits, look at the Actions tab for a Pages build run. Commits pushed with the default token sometimes do not trigger one; the fix is a personal access token, or a deploy step in the workflow.
- `docs/data.json` is rewritten on every update. GitHub Pages compresses it when serving.
- Open-Meteo's free API is non-commercial only, and the page footer carries the attribution.
- The basemap uses OpenStreetMap's public tiles. Check their usage policy if the page gets heavy traffic.
