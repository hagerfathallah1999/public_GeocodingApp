import streamlit as st
import requests
import geopandas as gpd
from streamlit_folium import folium_static
import leafmap.foliumap as leafmapap
import pandas as pd


@st.cache_data()
# load data in the first of app
def getCountriesData():
    countryPolygon = gpd.read_file(
        gpd.datasets.get_path('naturalearth_lowres'))
    return countryPolygon


def getCountryName(code):
    try:
        response = requests.get(f"https://restcountries.com/v2/alpha/{code}")
        response.raise_for_status()  # 404 error
    except requests.exceptions.HTTPError:
        return "Unknown"

    data = response.json()
    return data['name']


def getCountryDetails(nameOfCountry):
    restcountriesAPI = f"https://restcountries.com/v2/name/{nameOfCountry}"
    try:
        response = requests.get(restcountriesAPI)
        response.raise_for_status()  # 404 error
    except requests.exceptions.HTTPError:
        return "Sorry, no details found for this country, please try again.."

    dataOfCountry = response.json()[0]
    neighbors = [getCountryName(code)
                 for code in dataOfCountry.get('borders', [])]

    return {
        'name': dataOfCountry['name'].capitalize(),
        'capital': dataOfCountry['capital'],
        'population': dataOfCountry['population'],
        'region': dataOfCountry['region'],
        'subregion': dataOfCountry['subregion'],
        'languages': [lang['name'] for lang in dataOfCountry['languages']],
        'currencies': [cur['name'] for cur in dataOfCountry['currencies']],
        'neighbors': neighbors
    }


def app():
    st.title('Geocoding App')
    selectedCityInfoFromUser = getCountriesData()

    selectedContinentFromUser = st.selectbox(
        'Select a continent', selectedCityInfoFromUser.continent.unique())

    countriesInContinent = selectedCityInfoFromUser[selectedCityInfoFromUser.continent ==
                                                    selectedContinentFromUser]

    countryName = st.text_input('Enter a country name')
    if countryName:
        selectedCountry = countriesInContinent[countriesInContinent['name'].str.lower()
                                               == countryName.lower()]
        if len(selectedCountry) == 0:
            st.error('No results found')
        else:
            st.success(f'Selected country: {countryName}')
            country_details = getCountryDetails(countryName)
            st.subheader('Country Details')
            st.write('Name:', country_details['name'])
            st.write('Capital:', country_details['capital'])
            st.write('Population:', country_details['population'])
            st.write('Region:', country_details['region'])
            st.write('Subregion:', country_details['subregion'])
            st.write('Languages:', ", ".join(country_details['languages']))
            st.write('Currencies:', ", ".join(country_details['currencies']))

            neighbors = country_details['neighbors']
            if neighbors:
                selectedNeighbor = st.selectbox(
                    'Select a neighbor', ['None'] + neighbors)
                if selectedNeighbor != 'None':
                    st.write('Neighbor:', selectedNeighbor)
                    neighbor_data = selectedCityInfoFromUser[selectedCityInfoFromUser.name.str.lower(
                    ) == selectedNeighbor.lower()]

                    # create GeoDataFrame with selected country and neighbor
                    map_data = pd.concat([selectedCountry, neighbor_data])

                else:
                    st.write('No neighbors selected.')
                    # create GeoDataFrame with only selected country
                    map_data = selectedCountry

            else:
                st.write('No neighbors found.')
                # create GeoDataFrame with only selected country
                map_data = selectedCountry

            # Define style function for the map
            def style(x):
                return {'fillColor': '#FFFF00', 'fillOpacity': 0.5}

            # Create the map with the GeoDataFrame and the style function
            center_lat, center_lon = map_data.geometry.centroid.y.mean(
            ), map_data.geometry.centroid.x.mean()
            m = leafmapap.Map(center=[center_lat, center_lon], zoom=4)
            m.add_gdf(map_data, style_function=style)

            # Show the map
            folium_static(m)

            # Add download button
            geojson = map_data.to_json()
            file_name = f"{map_data.iloc[0]['name']}.geojson"
            st.download_button(
                label="Download GeoJSON",
                data=geojson,
                file_name=file_name,
                mime="application/json",
            )


if __name__ == '__main__':
    app()
