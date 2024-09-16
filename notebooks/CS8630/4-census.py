import pandas as pd
import requests
from bokeh.io import show, output_file
from bokeh.models import (
    ColorBar, LinearColorMapper, GeoJSONDataSource, HoverTool, LogColorMapper
)
from bokeh.palettes import Viridis256 as palette
from bokeh.plotting import figure
import json

# Step 1: Obtain Census Data
census_url = "https://api.census.gov/data/2020/dec/pl?get=P1_001N,NAME&for=state:*"
response = requests.get(census_url)
data = response.json()

# Convert the data into a pandas DataFrame
columns = data[0]
rows = data[1:]
df = pd.DataFrame(rows, columns=columns)

# Rename columns for clarity
df.rename(columns={'P1_001N': 'population', 'NAME': 'state_name'}, inplace=True)

# Convert population to integer
df['population'] = df['population'].astype(int)

# Standardize state names to title case
df['state_name'] = df['state_name'].str.title()

# Step 2: Load GeoJSON Data for US States
geojson_url = 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json'
geojson_response = requests.get(geojson_url)
us_states_geo = geojson_response.json()

# Remove Alaska, Hawaii, and Puerto Rico if desired
states_to_exclude = ['Alaska', 'Hawaii', 'Puerto Rico']
us_states_geo['features'] = [
    feature for feature in us_states_geo['features']
    if feature['properties']['name'] not in states_to_exclude
]

# Create a mapping from state names to populations
state_populations = df.set_index('state_name')['population'].to_dict()

# Add population data to GeoJSON properties
for feature in us_states_geo['features']:
    state_name = feature['properties']['name']
    population = state_populations.get(state_name, 0)
    feature['properties']['population'] = population

# Convert GeoJSON to a GeoJSONDataSource
geosource = GeoJSONDataSource(geojson=json.dumps(us_states_geo))

# Step 3: Create the Bokeh Visualization
palette = tuple(reversed(palette))

# Choose between Linear or Log Color Mapper
use_log_color_mapper = False  # Set to True if you prefer logarithmic scaling

if use_log_color_mapper:
    color_mapper = LogColorMapper(
        palette=palette,
        low=df['population'].min(),
        high=df['population'].max()
    )
else:
    color_mapper = LinearColorMapper(
        palette=palette,
        low=df['population'].min(),
        high=df['population'].max()
    )

# Create the figure
p = figure(
    title="2020 U.S. Census Population by State",
    toolbar_location="left",
    tools="pan,wheel_zoom,reset",
    width=800,
    height=500,
    match_aspect=True
)

# Add patches representing states
p.patches(
    'xs',
    'ys',
    source=geosource,
    fill_color={'field': 'population', 'transform': color_mapper},
    fill_alpha=0.7,
    line_color="white",
    line_width=0.5
)

# Add a hover tool
p.add_tools(HoverTool(tooltips=[
    ("State", "@name"),
    ("Population", "@population{,}"),
]))

# Add a color bar without specifying the ticker
color_bar = ColorBar(
    color_mapper=color_mapper,
    location=(0, 0),
    label_standoff=12,
    border_line_color=None
)
p.add_layout(color_bar, 'right')

# Output the visualization
output_file("census_population.html")
show(p)