import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st
from retrying import retry

population = pd.read_csv('resources/demographics_sk.csv')


def format_timestamp(s):
    return s.strftime("%Y-%m-%d")


@st.cache(show_spinner=False, max_entries=1, ttl=3600)
@retry(wait_fixed=1000, stop_max_attempt_number=10)
def get_infection_data():
    ag_tests = pd.read_csv(
        "https://raw.githubusercontent.com/Institut-Zdravotnych-Analyz/"
        "covid19-data/main/AG_Tests/OpenData_Slovakia_Covid_AgTests_District.csv",
        sep=";", parse_dates=[0])[['Date', 'District', 'Ag_Pos']]
    pcr_tests = pd.read_csv(
        "https://raw.githubusercontent.com/Institut-Zdravotnych-Analyz/"
        "covid19-data/main/PCR_Tests/OpenData_Slovakia_Covid_PCRTests_District.csv",
        sep=";", parse_dates=[0])[['Date', 'District', 'PCR_Pos']]

    districts = pd.DataFrame(population['District'], columns=['District'])
    dates = pd.DataFrame(pd.date_range(end=pcr_tests['Date'].max(), periods=7), columns=['Date'])
    frame = pd.merge(dates, districts, how='cross')

    daily_cases = frame.merge(pcr_tests, on=['Date', 'District'], how='left')
    daily_cases = daily_cases.merge(ag_tests, on=['Date', 'District'], how='left')
    daily_cases['total_positive'] = daily_cases['Ag_Pos'] + daily_cases['PCR_Pos']

    cases = daily_cases.groupby(['District'])['total_positive'].sum()
    start_date = dates['Date'].get(0)
    end_date = dates['Date'].get(len(dates) - 1)

    return cases, format_timestamp(start_date), format_timestamp(end_date)


def get_prevalence(cases, ascertainment_bias):
    prevalence = ascertainment_bias * cases / population.set_index('District').squeeze()
    return prevalence


def get_centroids(geo_data):
    centroids = geo_data["geometry"].to_crs(epsg=3035).centroid.to_crs(epsg=4326)
    return centroids.x, centroids.y


@st.cache(show_spinner=False, max_entries=1)
def get_districts():
    districts = gpd.read_file("https://raw.githubusercontent.com/drakh/"
                              "slovakia-gps-data/master/"
                              "GeoJSON/epsg_4326/districts_epsg_4326.geojson")[['NM3', 'geometry']]
    districts = districts.rename({'NM3': 'District'}, axis=1)
    districts['District'] = 'Okres ' + districts['District']
    districts["lon"], districts["lat"] = get_centroids(districts)
    return districts


def get_probabilities(prevalence, nr_of_people):
    probability = (1 - (1 - prevalence).pow(nr_of_people)).rename('estimate').reset_index()
    probability["estimate_pct"] = (100 * probability["estimate"]).round(2).astype(str) + "%"
    return probability


def get_chart_data(prevalence, nr_of_people):
    districts = get_districts()
    probability = get_probabilities(prevalence, nr_of_people)
    districts = districts.merge(probability)
    return districts


def get_pydeck_chart(prevalence, nr_of_people):
    probabilities = get_chart_data(prevalence, nr_of_people)
    deck = pdk.Deck(
        tooltip={
            "text": "{District}: {estimate_pct}",
        },
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(latitude=48.75,
                                         longitude=19.5,
                                         zoom=7,
                                         min_zoom=7,
                                         max_zoom=10,
                                         height=750
                                         ),
        layers=[
            pdk.Layer(
                'GeoJsonLayer',
                data=probabilities,
                getLineWidth=35,
                get_fill_color='[187, 30, 16, 255 * estimate]',
                pickable=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=probabilities,
                sizeMinPixels=10,
                sizeMaxPixels=18,
                get_position=['lon', 'lat'],
                get_text='estimate_pct',
            )
        ],
    )

    return deck
