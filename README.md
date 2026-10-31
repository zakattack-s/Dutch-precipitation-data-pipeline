# Dutch Precipitation Data Pipeline

## Project Overview

This project demonstrates Python-based data pipeline development through the collection, processing, and visualization of historical and incremental precipitation data across the Netherlands.

The project uses the Open-Meteo ECMWF IFS weather model to collect precipitation data and transform it into a geospatial dataset for visualization through an interactive map.

AI tools were used as learning support during development and to assist with building the HTML file for the interactive map.

## Project Features

- **Weather Data Collection:** Retrieve historical precipitation data from the Open-Meteo API.
- **Batch Processing:** Collect data across geographical grid cells while managing API request limits.
- **Incremental Updates:** Update the existing dataset without repeatedly downloading the entire historical record.
- **Geospatial Processing:** Generate Voronoi polygons to represent precipitation data across the Netherlands.
- **Interactive Visualization:** Explore precipitation patterns through an interactive map.

## Technologies

| Technology | Purpose |
|---|---|
| Python | Pipeline development |
| Pandas | Data processing and transformation |
| Requests | API integration |
| Parquet | Data storage |
| GeoPandas | Geospatial processing |
| Open-Meteo ECMWF IFS | Precipitation data source |
| HTML | Interactive map visualization |

## Interactive Map

Explore the precipitation data through the interactive map:

[View Interactive Map](./docs/index.html)

## Technical Documentation

For a detailed explanation of the pipeline architecture, development process, data preparation, and ingestion logic, see:

[Technical Documentation](Dutch-precipitation-data-pipeline/Readme.md)

## Project Status

This project is a work in progress. Additional pipeline improvements, documentation, and visualization features will be added as development continues.

## Acknowledgements

- [Open-Meteo](https://open-meteo.com/) for providing historical weather data.
