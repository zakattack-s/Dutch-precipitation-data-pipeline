# Pipeline Development

The project consists of two main stages: **initial data preparation** and a **recurring data pipeline**.

The initial preparation involved establishing the geographical grid, retrieving historical precipitation data, and generating the geographical polygons used for visualization. These steps were performed once to establish the project's initial dataset.

The recurring pipeline builds on this prepared dataset. It incrementally retrieves new precipitation data, transforms the updated dataset into a format suitable for the interactive map, and publishes the changes through GitHub Actions.

The precipitation data comes from the **ECMWF IFS model** (about 8 km grid cells) through the [Open-Meteo](https://open-meteo.com/) Historical Weather API. The following sections describe both stages and the technical decisions involved in their development.

## Repository structure

| Path | Purpose |
|---|---|
| `Preparations.ipynb` | One-time preparation: grid, historical download, polygons |
| `ifs_cells.parquet` | The model grid cells (`cell_id`, `lat`, `lon`) |
| `ifs_cell_polygons.geojson` | One Voronoi polygon per grid cell |
| `nl_rain_ifs.parquet` | The full precipitation dataset (`date`, `cell_id`, `rain_mm`) |
| `update_ifs.py` | Incremental ingestion script |
| `build_data.py` | Converts the dataset into the files used by the map |
| `prepare_places.py` | Optional: builds the municipality and city files for the map's dropdowns |
| `docs/` | The published website: `index.html`, `data.json`, `cells.geojson` |
| `.github/workflows/update.yml` | The GitHub Actions workflow |

## 1. Grid Preparation

The first step was to prepare a geographical grid covering the Netherlands.

The preparation process is documented in [Preparations.ipynb](Preparations.ipynb).

Open-Meteo does not provide a downloadable list of all its model grid coordinates through the API. Instead, when given geographical coordinates, the API returns data for the nearest available model grid point.

To work around this limitation, I:

1. Created my own grid of points covering the Netherlands (629 points inside or touching the border).
2. Sent the coordinates of each point to the Open-Meteo API for a single day.
3. Retrieved the actual model coordinates returned by the API.
4. Removed duplicates, which reduced the 629 points to 438 distinct model cells.
5. Stored these cell centers, with a numeric `cell_id`, for use in all later steps.

Points over water are snapped to the nearest land cell by the API, which explains most of the duplicates and the few large offsets between a requested point and the cell it returned.

### Choice of model

Three models were tested before choosing ECMWF IFS:

- **ERA5** (about 25 km) works, but the cells are too coarse for a map of the Netherlands.
- **ERA5-Land** (about 10 km) returned no precipitation values through this API.
- **ECMWF IFS** (about 8 km) returned complete data that correlated closely with ERA5 (daily correlation 0.85 to 0.95 in the months compared at one location) and was tested back to mid-2017.

Because different models disagree in detail, data from different models is never mixed in the same dataset.

## 2. Historical Data Ingestion

After preparing the grid, I downloaded historical precipitation data from 2023 to the present.

The ingestion process uses batching and chunking to divide the geographical grid into smaller groups of locations. Each request contains a batch of cells, and the history was saved in one file per batch and year. This avoids sending excessively large API requests, helps manage Open-Meteo's rate limits, and means an interrupted download can resume without repeating finished work.

The chunks were then merged into a single Parquet file, `nl_rain_ifs.parquet`, with one row per cell per day. Parquet keeps the file small and quick to read.

## 3. Geospatial Processing

To visualize the precipitation data across the Netherlands, I generated Voronoi polygons from the model grid coordinates.

Each polygon represents the geographical area closest to its grid point, which is also how the API assigns a location to a model cell. These polygons allow precipitation measurements to be displayed as spatial areas rather than individual points on the map.

The geometry work is done in the Dutch metric coordinate system (EPSG:28992), because distances in degrees are distorted at this latitude. The polygons are then clipped to the national border, slightly simplified (200 m) to keep the file small, converted back to latitude and longitude, and stored in GeoJSON format with their `cell_id`.

## 4. Incremental Data Ingestion

Once the historical dataset was created, I developed a separate script for incremental updates.

The script follows the same batching approach as the historical ingestion process, but instead of downloading the entire dataset again, it:

1. Reads the existing Parquet dataset.
2. Identifies the latest date that **every** grid cell has (the smallest of the per-cell latest dates).
3. Calculates the date range that needs updating.
4. Assumes Open-Meteo's data lags about five days behind the present (a setting in the script) and does not request newer days.
5. Re-downloads the last few days to account for potential historical revisions.
6. Keeps only the days for which every cell has a value, so a cell that is temporarily behind can never leave a permanent gap.
7. Combines the new data with the existing dataset, removes duplicates, and saves the updated file.

The file is written to a temporary name and then renamed, so a failed run cannot leave a half-written dataset. Requests use short connection timeouts and retries, because the shared GitHub runners occasionally stalled when connecting to the API. If a batch fails after all retries, the script exits with an error and saves nothing, which makes the workflow run show as failed.

The incremental ingestion script is available in [update_ifs.py](update_ifs.py).

This approach avoids unnecessary historical downloads while keeping the dataset up to date.

## 5. Data Transformation for Visualization

After updating the historical dataset, the next step is to prepare the data for the interactive map.

The raw precipitation dataset contains one record per grid cell per day. While this format is suitable for historical storage and analysis, it is not optimized for loading large time-series datasets in a web browser.

To address this, I developed [build_data.py](build_data.py), which transforms the raw Parquet dataset into a compact JSON file.

The transformation process:

1. Reads the updated precipitation dataset.
2. Removes duplicate records and sorts the data.
3. Restructures the dataset into a date-by-cell matrix covering every day in the range.
4. Fills missing measurements with `-1`.
5. Converts precipitation measurements into integer values representing tenths of a millimeter.
6. Exports the resulting dataset to `docs/data.json`.

The script also copies the Voronoi polygons into the `docs` directory as `docs/cells.geojson`, making both the geographical boundaries and precipitation data available to the web map.

The structure of `data.json` is:

```json
{
  "dates": ["2023-01-01", "2023-01-02", "..."],
  "ids":   [0, 1, 2, "..."],
  "v":     [[12, 0, 35, "..."], [10, 0, 28, "..."], "..."]
}
```

`v[i][d]` is the rain of cell `ids[i]` on day `dates[d]`, in tenths of a millimeter (`12` means 1.2 mm), or `-1` if there is no data. Integers keep the file small, and the matrix layout lets the map read one day for all cells with a single lookup per cell.

This separates the historical data storage format from the format used for visualization.

## 6. Making the Interactive Map

The map is a single static page, [docs/index.html](docs/index.html), built with the [Leaflet](https://leafletjs.com/) library and OpenStreetMap background tiles. It needs no server or database. The browser downloads `cells.geojson` and `data.json` and does everything else itself.

The HTML file was developed with AI assistance. I designed the data flow and checked the behavior; the page works as follows:

1. **Draw once.** The polygons from `cells.geojson` are added to the map a single time.
2. **Recolor on change.** When the selected day changes, the page looks up that day's values for every cell and updates only the polygon colors. Redrawing the shapes each time would be much slower.
3. **Match by `cell_id`.** The `ids` list in `data.json` links each polygon to its row in the data matrix.
4. **Fixed color scale.** Colors run from very light blue to dark blue on a square-root scale between 0 and 25 mm per day, with the same range for every day so that days can be compared by color. The square root spreads out the many low-rain days that a linear scale would show as nearly white. Cells with no data are gray.

The interface offers:

- a slider, previous and next buttons, a date picker, and a "Latest" button for choosing the day,
- a tooltip and an outline highlight when hovering over a cell,
- city names on a separate map layer above the polygons, so they stay readable,
- optional dropdowns to jump to a city or a municipality, and a switch to show all municipal boundaries.

The dropdowns read two extra files if they exist (`docs/cities.json` and `docs/municipalities.geojson`), created by [prepare_places.py](prepare_places.py). When the files are missing, the dropdowns stay hidden and the rest of the map works as normal.

To test the page locally, run `python build_data.py`, then `python -m http.server 8000` inside the `docs` folder, and open `http://localhost:8000`. Opening `index.html` directly does not work, because browsers block loading data files from local paths.

## 7. Automated Pipeline Updates with GitHub Actions

To automate the data ingestion and visualization process, I configured a GitHub Actions workflow, defined in [.github/workflows/update.yml](.github/workflows/update.yml).

### Triggers

The workflow runs on the 1st, 11th, and 21st of each month at 06:00 UTC, which is roughly every ten days (GitHub's schedule syntax cannot express an exact ten-day interval). It can also be started manually from the Actions tab.

### The update job

Each run starts a fresh Ubuntu machine and:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Installs the required dependencies (`pandas`, `pyarrow`, `requests`).
4. Executes `update_ifs.py` to retrieve new precipitation data.
5. Executes `build_data.py` to regenerate the web map dataset.
6. Commits and pushes the updated Parquet file and `docs` files to the repository, if changes were detected.

The project lives in a subfolder of the repository, so the job sets that folder as its working directory. The job has a 30-minute time limit, so a stuck run cannot use up the free minutes.

### The deploy job

A second job, which runs only if the update job succeeds, publishes the `docs` folder to GitHub Pages. GitHub Pages' simple "deploy from a branch" mode only supports a `docs` folder at the top level of the repository, so the site is deployed with GitHub Actions instead (repository Settings, Pages, Source: GitHub Actions). Doing the deployment in the same workflow also means that the site is rebuilt right after the data changes, without relying on a commit made by the workflow to trigger anything.

### Permissions and failure handling

The workflow needs write access to the repository contents (to commit the new data) and to GitHub Pages (to deploy). These are declared at the top of the file, and the repository's workflow permissions must be set to read and write.

A failed update run saves nothing and leaves the previous dataset and website untouched. The next scheduled run recovers automatically, because the incremental script restarts from the oldest day that any cell is missing.

This allows the dataset and interactive map to be updated without manually running the pipeline on my local machine.

## 8. Pipeline Architecture

The project has two stages:

**Initial preparation**

```text
Preparations.ipynb
        |
        v
Geographical Grid
        |
        +----------------------+
        |                      |
        v                      v
Historical Data         Voronoi Polygons
        |                      |
        v                      v
nl_rain_ifs.parquet   ifs_cell_polygons.geojson
        |                      |
        +----------+-----------+
                   |
                   v
             build_data.py
                   |
                   v
       docs/data.json + docs/cells.geojson
                   |
                   v
           Interactive Map
```

**Recurring pipeline**

```text
GitHub Actions (1st, 11th, 21st, or manual)
      |
      v
update job:  update_ifs.py
      |
      v
Updated Parquet Dataset
      |
      v
build_data.py
      |
      v
docs/data.json + docs/cells.geojson
      |
      v
Commit and push to the repository
      |
      v
deploy job:  publish docs/ to GitHub Pages
      |
      v
Interactive Map (live website)
```

The initial preparation establishes the data and geographical structure. The recurring pipeline updates the precipitation data and regenerates the files used by the interactive map.

## 9. Limitations and Attribution

- **Model data, not observations.** The values come from the ECMWF IFS model, not from rain gauges or radar, and are shown at about 8 km resolution. They show broad regional patterns, not local showers.
- **Not exactly every ten days.** The schedule runs on fixed days of the month, so the gap varies, and GitHub may start a run a little late.
- **Data delay.** The newest days shown on the map are about five days behind the present.
- **Dataset growth.** `data.json` is rewritten on every update and grows with each added day.
- **Attribution.** Weather data is provided by [Open-Meteo](https://open-meteo.com/) under CC BY 4.0, for non-commercial use. Map tiles are © OpenStreetMap contributors. The map footer credits both.
