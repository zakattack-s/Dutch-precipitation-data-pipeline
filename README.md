# Dutch Precipitation Data Pipeline

An automated Python pipeline that collects daily precipitation data for the Netherlands, stores it as a geospatial dataset, and publishes it as an interactive map that updates itself.

**[View the live interactive map](https://zakattack-s.github.io/Dutch-precipitation-data-pipeline/)**

## Project Overview

This project demonstrates Python-based data pipeline development: collecting historical and incremental precipitation data, transforming it into a geospatial dataset, and visualizing it on an interactive map.

Rainfall data comes from the **ECMWF IFS weather model** through the [Open-Meteo](https://open-meteo.com/) API. It covers the Netherlands with 438 model grid cells of about 8 km each, with daily values from 2023 to the present. The map shows each cell as a polygon colored by the rain that fell on the selected day.

A scheduled GitHub Actions workflow keeps everything current: it downloads the newest days, rebuilds the map data, and republishes the website without any manual work.

AI tools were used as learning support during development and to assist with building the HTML file for the interactive map.

## Project Features

- **Weather Data Collection:** Retrieve historical precipitation data from the Open-Meteo API.
- **Batch Processing:** Collect data across geographical grid cells while managing API request limits.
- **Incremental Updates:** Update the existing dataset without repeatedly downloading the entire historical record, with safeguards against gaps and duplicate rows.
- **Geospatial Processing:** Generate Voronoi polygons to represent precipitation data across the Netherlands.
- **Interactive Visualization:** Explore precipitation patterns day by day, using a slider or a date picker, with a tooltip for every cell.
- **Automation:** A GitHub Actions workflow runs on the 1st, 11th, and 21st of each month, updates the data, and deploys the map to GitHub Pages.

## How It Works

```text
Open-Meteo API  ->  update_ifs.py  ->  Parquet dataset  ->  build_data.py  ->  JSON + GeoJSON  ->  Interactive map
                    (incremental)      (one row per        (compact format    (docs/ folder)      (GitHub Pages)
                                        cell per day)       for the browser)
                                         ^
                                         |
                              GitHub Actions runs the whole chain on a schedule
```

## Technologies

| Technology | Purpose |
|---|---|
| Python | Pipeline development |
| Pandas | Data processing and transformation |
| Requests | API integration |
| Parquet | Data storage |
| GeoPandas | Geospatial processing |
| GeoJSON | Geographical boundaries for the map |
| Open-Meteo ECMWF IFS | Precipitation data source |
| HTML and JavaScript (Leaflet) | Interactive map visualization |
| GitHub Actions | Scheduled data updates and deployment |
| GitHub Pages | Hosting for the interactive map |

## Interactive Map

Explore the precipitation data through the interactive map:

[View Interactive Map](https://zakattack-s.github.io/Dutch-precipitation-data-pipeline/)

## Technical Documentation

For a detailed explanation of the pipeline architecture, development process, data preparation, ingestion logic, map construction, and the automated workflow, see:

[Technical Documentation](Dutch-precipitation-data-pipeline/Readme.md)

## Data Notes

- The values are **model data**, not rain gauge or radar measurements, and are shown at about 8 km resolution. The map shows broad regional patterns, not local showers.
- The newest days on the map are about five days behind the present.

## Project Status

This project is a work in progress. Additional pipeline improvements, documentation, and visualization features will be added as development continues.

## Acknowledgements

- [Open-Meteo](https://open-meteo.com/) for providing historical weather data (CC BY 4.0, non-commercial use).
- [ECMWF](https://www.ecmwf.int/) for the IFS model that the data originates from.
- [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors for the map background.
- [Leaflet](https://leafletjs.com/) for the interactive map library.
