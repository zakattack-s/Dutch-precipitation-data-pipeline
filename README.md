# Dutch Precipitation Data Pipeline

## Project Overview

This project demonstrates Python-based data pipeline development, including API integration, batch processing, historical data ingestion, incremental updates, and geospatial data processing.

The objective is to build a pipeline that collects precipitation data across the Netherlands and visualizes it through an interactive map.

AI tools were used as learning support throughout the project and to assist with building the HTML file for the interactive map. The data pipeline development and underlying logic were the main focus of the project.

## Technology Choices and Approaches

Several data sources and approaches were explored before selecting the final solution.

- **KNMI:** Initially considered using KNMI weather data. However, its data downloads involve large ZIP files, which seemed unnecessarily resource-intensive for a project that only needs to update a few days of data at a time.
- **Open-Meteo ERA5:** An alternative approach using the ERA5 model and its approximately 25 km grid was tested. However, the spatial resolution did not provide the level of detail I wanted for the visualization.
- **Open-Meteo ECMWF IFS:** The final approach uses the ECMWF IFS model, with a grid resolution of approximately 9–11 km, providing a better level of spatial detail for this project.

## Pipeline Development

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
