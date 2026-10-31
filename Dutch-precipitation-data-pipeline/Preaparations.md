# Pipeline Development

### 1. Grid Preparation

The first step was to prepare a geographical grid covering the Netherlands.

The preparation process is documented in [Preparation file](Dutch-precipitation-data-pipeline/Preparations.ipynb).

Open-Meteo does not provide a downloadable list of all its model grid coordinates through the API. Instead, when given geographical coordinates, the API returns data for the nearest available model grid point.

To work around this limitation, I:

1. Created my own grid covering the Netherlands.
2. Sent the coordinates of each grid point to the Open-Meteo API.
3. Retrieved the actual model coordinates returned by the API.
4. Stored these coordinates for use in subsequent data ingestion.

This provided a consistent set of model grid locations to use throughout the pipeline.

### 2. Historical Data Ingestion

After preparing the grid, I downloaded historical precipitation data from 2023 to the present.

The ingestion process uses batching and chunking to divide the geographical grid into smaller groups of locations. This avoids sending excessively large API requests and helps manage API rate limits.

The collected data is stored in Parquet format for efficient storage and subsequent processing.

### 3. Geospatial Processing

To visualize the precipitation data across the Netherlands, I generated Voronoi polygons from the model grid coordinates.

Each polygon represents the geographical area associated with its corresponding grid point. These polygons allow precipitation measurements to be displayed as spatial areas rather than individual points on the map.

### 4. Incremental Data Ingestion

Once the historical dataset was created, I developed a separate script for incremental updates.

The script follows the same batching approach as the historical ingestion process, but instead of downloading the entire dataset again, it:

1. Reads the existing Parquet dataset.
2. Identifies the latest date available across all grid cells.
3. Calculates the date range that needs updating.
4. Accounts for Open-Meteo's approximately five-day data delay.
5. Re-downloads the last few days to account for potential historical revisions.
6. Combines the new data with the existing dataset, removes duplicates, and saves the updated file.

The incremental ingestion script is available in [update_ifs.py](Dutch-precipitation-data-pipeline/update_ifs.py).

This approach avoids unnecessary historical downloads while keeping the dataset up to date.
