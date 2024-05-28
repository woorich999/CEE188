import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins

# Load the necessary data
columns_to_keep = ['Plant_annual_NOx_emissions__tons_', 'latitude', 'longitude', 'GEOID10', 'TOTAL_POP', 'NH_WHITE_A', 'NH_BLACK_A', 'NH_NAM_NAK', 'NH_ASIAN_A', 'NH_NHI_PI_', 'HL_TOT', 'Raw_data_for_Low_Income_Population']
halfdata = pd.read_csv('C:/Users/ajall/Downloads/CEE188_WEACT_0.5miles.csv', usecols=columns_to_keep)
halfdata = halfdata.dropna()
halfdata['GEOID10'] = halfdata['GEOID10'].astype(str).str[:-2]

halfdata['White%'] = halfdata['NH_WHITE_A'] / halfdata['TOTAL_POP'] * 100
halfdata['Black%'] = halfdata['NH_BLACK_A'] / halfdata['TOTAL_POP'] * 100
halfdata['Native American%'] = halfdata['NH_NAM_NAK'] / halfdata['TOTAL_POP'] * 100
halfdata['Asian%'] = halfdata['NH_ASIAN_A'] / halfdata['TOTAL_POP'] * 100
halfdata['Pacific Islander%'] = halfdata['NH_NHI_PI_'] / halfdata['TOTAL_POP'] * 100
halfdata['Hispanic%'] = halfdata['HL_TOT'] / halfdata['TOTAL_POP'] * 100

columns_to_drop = ['NH_WHITE_A', 'NH_BLACK_A', 'NH_NAM_NAK', 'NH_ASIAN_A', 'NH_NHI_PI_', 'HL_TOT']
halfdata.drop(columns=columns_to_drop, inplace=True)

cali = gpd.read_file("C:/Users/ajall/Downloads/tl_rd22_06_tract.zip")
cali['geometry'] = cali['geometry'].simplify(tolerance=0.001, preserve_topology=True)
cali['GEOID'] = cali['GEOID'].astype(str).str[:-1]

dataCalifornia = pd.read_csv('C:/Users/ajall/Downloads/DECENNIALDP2020.DP1_2024-05-25T065010/DECENNIALDP2020.DP1-Data.csv', dtype={'FIPS': str})
race_columns = ['GEO_ID', 'DP1_0076C', 'DP1_0105C', 'DP1_0087C', 'DP1_0088C', 'DP1_0089C', 'DP1_0090C', 'DP1_0096C']
raceCalifornia = dataCalifornia[race_columns]

raceCalifornia.columns = ['GEOID', 'Total Population', 'White', 'Black', 'Native American', 'Asian', 'Pacific Islander', 'Hispanic or Latino']
raceCalifornia.loc[:, 'GEOID'] = raceCalifornia['GEOID'].str.replace('1400000US', '', regex=False)
raceCalifornia.loc[:, 'GEOID'] = raceCalifornia['GEOID'].apply(lambda x: x[:-1])

caliRace = cali.merge(raceCalifornia, on='GEOID')
caliRace.drop(columns=['STATEFP', 'COUNTYFP', 'NAME', 'NAMELSAD', 'MTFCC', 'FUNCSTAT', 'AWATER', 'INTPTLAT', 'INTPTLON'], inplace=True)

caliRace['PCT_White'] = caliRace['White'] / caliRace['Total Population'] * 100
caliRace['PCT_Black'] = caliRace['Black'] / caliRace['Total Population'] * 100
caliRace['PCT_NativeAmerican'] = caliRace['Native American'] / caliRace['Total Population'] * 100
caliRace['PCT_Asian'] = caliRace['Asian'] / caliRace['Total Population'] * 100
caliRace['PCT_PacificIslander'] = caliRace['Pacific Islander'] / caliRace['Total Population'] * 100
caliRace['PCT_Hispanic'] = caliRace['Hispanic or Latino'] / caliRace['Total Population'] * 100

caliRace.drop(columns=['White', 'Black', 'Native American', 'Asian', 'Pacific Islander', 'Hispanic or Latino'], inplace=True)

m = folium.Map(location=[36.7378, -119.7871], zoom_start=6, tiles='CartoDB positron', attribution='CartoDB')

percentiles = np.percentile(halfdata['Plant_annual_NOx_emissions__tons_'], [25, 50, 75])

def get_color(emission, percentiles):
    if emission < percentiles[0]:
        return 'green'
    elif emission < percentiles[1]:
        return 'yellow'
    elif emission < percentiles[2]:
        return 'orange'
    else:
        return 'red'

def get_tooltip(row):
    tooltip = f"""
    <strong>NOx emissions:</strong> {row['Plant_annual_NOx_emissions__tons_']} tons<br>
    <strong>White:</strong> {row['White%']:.1f}%<br>
    <strong>Black:</strong> {row['Black%']:.1f}%<br>
    <strong>Asian:</strong> {row['Asian%']:.1f}%<br>
    <strong>Native American:</strong> {row['Native American%']:.1f}%<br>
    <strong>Pacific Islander:</strong> {row['Pacific Islander%']:.1f}%<br>
    <strong>Hispanic:</strong> {row['Hispanic%']:.1f}%<br>
    <strong>Low Income:</strong> {row['Raw_data_for_Low_Income_Population']*100}%
    """
    return tooltip

# Create a FeatureGroup for NOx emissions
emissions_layer = folium.FeatureGroup(name="NOx Emissions")

for idx, row in halfdata.iterrows():
    color = get_color(row['Plant_annual_NOx_emissions__tons_'], percentiles)
    tooltip = get_tooltip(row)
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=6,
        color=None,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=f"NOx emissions: {row['Plant_annual_NOx_emissions__tons_']} tons",
        tooltip=folium.Tooltip(tooltip)
    ).add_to(emissions_layer)

emissions_layer.add_to(m)

# Add choropleth layers
folium.Choropleth(
    geo_data=caliRace,
    data=caliRace,
    key_on='feature.properties.GEOID',
    columns=['GEOID', 'PCT_White'],
    fill_color='Blues',
    line_weight=0.1,
    fill_opacity=0.8,
    line_opacity=0.2,
    name="White %"
).add_to(m)

folium.Choropleth(
    geo_data=caliRace,
    data=caliRace,
    key_on='feature.properties.GEOID',
    columns=['GEOID', 'PCT_Black'],
    fill_color='Oranges',
    line_weight=0.1,
    fill_opacity=0.8,
    line_opacity=0.2,
    name="Black %"
).add_to(m)

folium.Choropleth(
    geo_data=caliRace,
    data=caliRace,
    key_on='feature.properties.GEOID',
    columns=['GEOID', 'PCT_Asian'],
    fill_color='Reds',
    line_weight=0.1,
    fill_opacity=0.8,
    line_opacity=0.2,
    name="Asian %"
).add_to(m)

folium.Choropleth(
    geo_data=caliRace,
    data=caliRace,
    key_on='feature.properties.GEOID',
    columns=['GEOID', 'PCT_Hispanic'],
    fill_color='Greens',
    line_weight=0.1,
    fill_opacity=0.8,
    line_opacity=0.2,
    name="Hispanic %"
).add_to(m)

# Add minimap
minimap = plugins.MiniMap()
m.add_child(minimap)

# Add layer control
folium.LayerControl(position='topright', collapsed=True, autoZIndex=True).add_to(m)

# Save the map
m.save('california_distribution_map.html')
