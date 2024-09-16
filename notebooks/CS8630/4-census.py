import pandas as pd
import requests

from bokeh.io import show, output_file
from bokeh.models import ColorBar, LogColorMapper, HoverTool
from bokeh.palettes import Viridis6 as palette
from bokeh.plotting import figure
from bokeh.sampledata.us_states import data as states
# Add a color bar
from bokeh.models import LinearColorMapper

# API endpoint for 2020 state population data
url = "https://api.census.gov/data/2020/dec/pl?get=P1_001N,NAME&for=state:*"

response = requests.get(url)
data = response.json()

# Convert the data into a pandas DataFrame
columns = data[0]
rows = data[1:]
df = pd.DataFrame(rows, columns=columns)

# Rename columns for clarity
df.rename(columns={'P1_001N': 'population', 'NAME': 'state'}, inplace=True)

# Convert population to integer
df['population'] = df['population'].astype(int)



# Remove states not in the contiguous U.S.
excluded_states = ["AK", "HI", "PR"]
states = {code: state for code, state in states.items() if code not in excluded_states}

# Map state names to their codes
state_xs = [state["lons"] for state in states.values()]
state_ys = [state["lats"] for state in states.values()]
state_names = [state["name"] for state in states.values()]
state_abbrevs = list(states.keys())

# Create a DataFrame for the map data
map_data = pd.DataFrame({
    'state_code': state_abbrevs,
    'state_name': state_names,
    'x': state_xs,
    'y': state_ys
})

# Merge with the census data
merged_data = pd.merge(map_data, df, how='left', left_on='state_name', right_on='state')


# Reverse the palette so higher populations are darker
palette = tuple(reversed(palette))

# Create a color mapper
color_mapper = LogColorMapper(palette=palette)

# Create the figure
p = figure(title="2020 U.S. Census Population by State", 
           toolbar_location="left", plot_width=800, plot_height=500)

# Add patches representing states
p.patches('x', 'y', source=merged_data,
          fill_color={'field': 'population', 'transform': color_mapper},
          fill_alpha=0.7, line_color="white", line_width=0.5)

# Add a hover tool
p.add_tools(HoverTool(tooltips=[
    ("State", "@state_name"),
    ("Population", "@population{,}"),
]))



color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0),
                     ticker={'base': 10, 'desired_num_ticks': 10})
p.add_layout(color_bar, 'right')

# Output the visualization
output_file("census_population.html")
show(p)