# Pipeline Development

The project consists of two main stages: **initial data preparation** and a **recurring data pipeline**.

The initial preparation involved establishing the geographical grid, retrieving historical precipitation data, and generating the geographical polygons used for visualization. These steps were performed once to establish the project's initial dataset.

The recurring pipeline builds on this prepared dataset. It incrementally retrieves new precipitation data, transforms the updated dataset into a format suitable for the interactive map, and publishes the changes through GitHub Actions.

The following sections describe both stages and the technical decisions involved in their development.

## 1. Grid Preparation

The first step was to prepare a geographical grid covering the Netherlands.

The preparation process is documented in [Preparations.ipynb](Preparations.ipynb).

Open-Meteo does not provide a downloadable list of all its model grid coordinates through the API. Instead, when given geographical coordinates, the API returns data for the nearest available model grid point.

To work around this limitation, I:

1. Created my own grid covering the Netherlands.
2. Sent the coordinates of each grid point to the Open-Meteo API.
3. Retrieved the actual model coordinates returned by the API.
4. Stored these coordinates for use in subsequent data ingestion.

This provided a consistent set of model grid locations to use throughout the pipeline.

## 2. Historical Data Ingestion

After preparing the grid, I downloaded historical precipitation data from 2023 to the present.

The ingestion process uses batching and chunking to divide the geographical grid into smaller groups of locations. This avoids sending excessively large API requests and helps manage API rate limits.

The collected data is stored in Parquet format for efficient storage and subsequent processing.

## 3. Geospatial Processing

To visualize the precipitation data across the Netherlands, I generated Voronoi polygons from the model grid coordinates.

Each polygon represents the geographical area associated with its corresponding grid point. These polygons allow precipitation measurements to be displayed as spatial areas rather than individual points on the map.

The resulting polygons are stored in GeoJSON format for use in the interactive map.

## 4. Incremental Data Ingestion

Once the historical dataset was created, I developed a separate script for incremental updates.

The script follows the same batching approach as the historical ingestion process, but instead of downloading the entire dataset again, it:

1. Reads the existing Parquet dataset.
2. Identifies the latest date available across all grid cells.
3. Calculates the date range that needs updating.
4. Accounts for Open-Meteo's approximately five-day data delay.
5. Re-downloads the last few days to account for potential historical revisions.
6. Combines the new data with the existing dataset, removes duplicates, and saves the updated file.

The incremental ingestion script is available in [update_ifs.py](update_ifs.py).

This approach avoids unnecessary historical downloads while keeping the dataset up to date.

## 5. Data Transformation for Visualization

After updating the historical dataset, the next step is to prepare the data for the interactive map.

The raw precipitation dataset contains one record per grid cell per day. While this format is suitable for historical storage and analysis, it is not optimized for loading large time-series datasets in a web browser.

To address this, I developed [build_data.py](build_data.py), which transforms the raw Parquet dataset into a compact JSON file.

The transformation process:

1. Reads the updated precipitation dataset.
2. Removes duplicate records and sorts the data.
3. Restructures the dataset into a date-by-cell matrix.
4. Fills missing measurements with a designated value.
5. Converts precipitation measurements into integer values representing tenths of a millimeter.
6. Exports the resulting dataset to `docs/data.json`.

The script also copies the Voronoi polygons into the `docs` directory, making both the geographical boundaries and precipitation data available to the web map.

This separates the historical data storage format from the format used for visualization.

## 6. Interactive Map

The interactive map combines the geographical polygons with the processed precipitation data.

The map allows users to explore precipitation patterns across the Netherlands over time.

The HTML file was developed with AI assistance. The visualization uses the generated GeoJSON polygons and compact JSON dataset to display precipitation measurements through a time-based interface.

The map files are located in the `docs` directory.

## 7. Automated Pipeline Updates

To automate the data ingestion and visualization process, I configured a GitHub Actions workflow.

The workflow is scheduled to run on the 1st, 11th, and 21st of each month, with the option to trigger it manually.

Each scheduled run:

1. Checks out the repository.
2. Sets up the Python environment.
3. Installs the required dependencies.
4. Executes `update_ifs.py` to retrieve new precipitation data.
5. Executes `build_data.py` to regenerate the web map dataset.
6. Commits and pushes the updated data and map files to the repository, if changes were detected.

The workflow is defined in the GitHub Actions configuration file.

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
GitHub Actions
      |
      v
update_ifs.py
      |
      v
Updated Parquet Dataset
      |
      v
build_data.py
      |
      v
JSON + GeoJSON
      |
      v
Interactive Map
      |
      v
Commit and Publish
```

The initial preparation establishes the data and geographical structure. The recurring pipeline updates the precipitation data and regenerates the files used by the interactive map.

