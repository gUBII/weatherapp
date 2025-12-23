# Bangladesh Live Weather Dashboard

This is a Streamlit application that displays real-time weather data for major cities in Bangladesh. It also includes GIS features like overlaying boundary layers, drawing areas of interest (AOI), and generating choropleth maps.

This project uses the [Open-Meteo API](https://open-meteo.com/), which is free and does not require an API key.

## Project Structure

The project is structured as follows:

- `requirements.txt`: This file lists all the Python dependencies required to run the application.
- `src/`: This directory contains the source code for the application.
- `src/app.py`: This is the main application file that runs the Streamlit app.
- `src/config.py`: This file contains the configuration for the application, such as the list of cities.
- `src/weather_api.py`: This module handles all interactions with the Open-Meteo API.
- `src/weather_codes.py`: This file contains the mapping from WMO weather codes to human-readable strings.
- `src/gis.py`: This module provides GIS-related functionalities, such as handling GeoJSON files and performing spatial analysis.
- `src/ui.py`: This module contains functions for creating the user interface components of the Streamlit app.

## How to Run the Application

1.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Streamlit app:**

    ```bash
    streamlit run src/app.py
    ```

    This will start the application in your web browser.