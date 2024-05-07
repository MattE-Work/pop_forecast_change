
import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import pandas as pd
#import contextily as ctx
#import matplotlib.pyplot as plt
from streamlit_folium import folium_static
from streamlit_folium import st_folium
import altair as alt

import branca #customer colour scales

#----------------------------------------------
@st.cache_data(ttl=1800)
def load_shapefile(filename):
    return gpd.read_file(filename)

#----------------------------------------------

def render_map_with_count_by_lsoa(local_authority, count_data, lsoa_data):
    lsoa_data = lsoa_data[lsoa_data['LocalAuthority'] == local_authority]
    
    # Merge count data with LSOA data
    lsoa_data = lsoa_data.merge(count_data, on='LSOA11CD', how='left')
    
    # Create a folium map centered on the local authority
    m = folium.Map(location=[lsoa_data.centroid.y.mean(), lsoa_data.centroid.x.mean()], zoom_start=10)

    # Add LSOA boundaries
    folium.GeoJson(lsoa_data.to_json(),
                   tooltip=folium.GeoJsonTooltip(fields=['LSOA11NM', 'count'], localize=True),
                   ).add_to(m)

    # Add marker clusters for each LSOA
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each LSOA
    for idx, row in lsoa_data.iterrows():
        folium.Marker([row['geometry'].centroid.y, row['geometry'].centroid.x],
                      popup=f"<b>{row['LSOA11NM']}</b><br>Count: {row['count']}",
                      ).add_to(marker_cluster)

    return m

#----------------------------------------------

def render_folium_map(gdf, line_weight=1):
    """
    Render a Folium map with GeoDataFrame data.

    Parameters:
    - gdf (GeoDataFrame): GeoDataFrame containing the data to plot on the map.
    - line_weight (int): Thickness of the line (border) around the geometries.

    Returns:
    - None
    """
    # Set the CRS of the GeoDataFrame to EPSG 4326 (WGS 84) for Folium compatibility
    gdf = gdf.to_crs(epsg=4326)

    # Create a Folium map centered at the mean of the GeoDataFrame geometries
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10)

    # Add OpenStreetMap tiles as the background (base layer)
    folium.TileLayer('openstreetmap').add_to(m)

    # Add GeoDataFrame geometries to the map with specified line weight
    folium.GeoJson(gdf, style_function=lambda feature: {
        'color': 'black',  # Border color
        'weight': line_weight,  # Line weight
    }).add_to(m)

    # Render the map in Streamlit using streamlit_folium
    folium_static(m, width=1000, height=750)
    #st_folium(m, height='400')
    return m

#----------------------------------------------

def create_color_scale(gdf, column_name):
    """
    Create a fixed color scale for IMD quintiles ranging from 1 to 5, handling None values.

    Parameters:
    gdf (GeoDataFrame): GeoDataFrame containing the IMD data.
    column_name (str): Column name containing the IMD quintile data.

    Returns:
    branca.colormap.LinearColormap: Configured color scale.
    """
    # Ensure all data is valid and between 1 to 5
    valid_data = gdf.dropna(subset=[column_name])
    valid_data = valid_data[valid_data[column_name].between(1, 5)]

    # Define colors corresponding to IMD quintiles from 1 to 5
    colors = ['red', 'orange', 'yellow', 'lightgreen', 'darkgreen']
    # Quintile breaks (ensure this matches your data exactly)
    quintiles = [1, 2, 3, 4, 5]

    # Create a color scale with discrete colors and breaks
    #color_scale = branca.colormap.LinearColormap(
    #    colors=colors,
    #    vmin=min(quintiles),
    #    vmax=max(quintiles),
    #    index=quintiles,
    #    caption='IMD Quintile'
    #)
    color_scale = branca.colormap.LinearColormap(
        colors=colors,
        vmin=1,
        vmax=5,
        index=[1,2,3,4,5],
        caption='IMD Quintile'
    )
    
    # Customize the appearance
    color_scale.style = {
        'font-size': '10px',
        'font-family': 'Arial',
        'box-shadow': '2px 2px 2px lightgrey',
        'border-radius': '5px',
        'position': 'bottomright'
    }

    return color_scale

#----------------------------------------------

def create_diverging_color_scale(gdf, net_change_column):
    max_value = gdf[net_change_column].max()
    min_value = gdf[net_change_column].min()

    # Check the range of data and adjust indices accordingly
    if min_value >= 0:
        # All values are non-negative
        index = [min_value, max_value]
        colors = ['white', 'red']
    elif max_value <= 0:
        # All values are non-positive
        index = [min_value, max_value]
        colors = ['blue', 'white']
    else:
        # Values include both negative and positive
        index = [min_value, 0, max_value]
        colors = ['blue', 'white', 'red']

    # Define the color scale
    color_scale = branca.colormap.LinearColormap(
        colors=colors,
        vmin=min_value,
        vmax=max_value,
        index=index,
        caption='Population Change'
    )

    # Customize appearance
    color_scale.style = {
        'font-size': '10px',
        'font-family': 'Arial',
        'box-shadow': '2px 2px 2px lightgrey',
        'border-radius': '5px',
        'position': 'bottomright'
    }

    return color_scale


def render_folium_map_heatmap_net_change(gdf, change_column, line_weight=1, title='', LSOA_column = 'LSOA21CD'):
    """
    Render a Folium map with GeoDataFrame data and optional count data.

    Parameters:
    - gdf (GeoDataFrame): GeoDataFrame containing the data to plot on the map.
    - count_df (DataFrame, optional): DataFrame containing count data per LSOA.
    - line_weight (int): Thickness of the line (border) around the geometries.
    - color_scheme (str): Color scheme for the choropleth map. Default is 'YlOrRd'.

    Returns:
    - Folium Map object
    """
    st.subheader(title)
    # Set the CRS of the GeoDataFrame to EPSG 4326 (WGS 84) for Folium compatibility
    gdf = gdf.to_crs(epsg=4326) #testing handling outside of the function

    # Create and apply a diverging color scale
    color_scale = create_diverging_color_scale(gdf, change_column)

    # Create a Folium map centered at the mean of the GeoDataFrame geometries
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=8.5) #higher number zooms in, lower number zooms out

    # Add OpenStreetMap tiles as the background (base layer)
    folium.TileLayer('openstreetmap').add_to(m)

    # Use GeoJson to apply the style function
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': color_scale(feature['properties'][change_column]),
            'color': 'black',  # Border color
            'weight': line_weight,
            'fillOpacity': 0.7,
        },
        tooltip=folium.features.GeoJsonTooltip(fields=[LSOA_column, change_column],
                                               aliases=['LSOA Code', 'Net Change'],
                                               labels=True)
    ).add_to(m)

    # Add the color scale legend to the map
    color_scale.add_to(m)

    # Render the map in Streamlit using streamlit_folium
    #folium_static(m)#, width=400, height=750)
    folium_static(m, width=550, height=650)

    return m

#----------------------------------------------
"""
def prepare_data_for_map(gdf, list_column_names_to_keep):
    # Example transformation: convert GeoDataFrame to WGS 84 and extract necessary columns
    #example list_column_names_to_keep = ['LSOA11CD', 'geometry', 'count_column']
    #geometry must be a column name present in the gdf
    gdf = gdf.to_crs(epsg=4326)
    data_for_map = gdf[list_column_names_to_keep]
    
    # Convert geometry to WKT (Well-Known Text) format
    data_for_map['geometry'] = data_for_map['geometry'].apply(lambda x: x.wkt)
    return data_for_map
"""




def render_folium_map_heatmap(gdf, count_column=None, line_weight=1, color_scheme='YlOrRd', title='', LSOA_column = 'LSOA11CD'):
    """
    Render a Folium map with GeoDataFrame data and optional count data.

    Parameters:
    - gdf (GeoDataFrame): GeoDataFrame containing the data to plot on the map.
    - count_df (DataFrame, optional): DataFrame containing count data per LSOA.
    - line_weight (int): Thickness of the line (border) around the geometries.
    - color_scheme (str): Color scheme for the choropleth map. Default is 'YlOrRd'.

    Returns:
    - Folium Map object
    """
    st.subheader(title)
    # Set the CRS of the GeoDataFrame to EPSG 4326 (WGS 84) for Folium compatibility
    gdf = gdf.to_crs(epsg=4326) #testing handling outside of the function

    # Remove entries with None values in the count_column to prevent errors
    gdf = gdf.dropna(subset=[count_column])

    # Create a color scale specifically for IMD quintiles
    color_scale = create_color_scale(gdf, count_column)

    # Create a Folium map centered at the mean of the GeoDataFrame geometries
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=8.5) #higher number zooms in, lower number zooms out

    # Add OpenStreetMap tiles as the background (base layer)
    folium.TileLayer('openstreetmap').add_to(m)

    ## Add GeoDataFrame geometries to the map with specified line weight
    #folium.GeoJson(gdf, style_function=lambda feature: {
    #    'color': 'blue',  # Border color
    #    'weight': line_weight,  # Line weight
    #},
    #tooltip=folium.features.GeoJsonTooltip(fields=[LSOA_column, count_column],
    #aliases=['LSOA Code', 'Count'],
    #labels=True)
    #).add_to(m)

    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': color_scale(feature['properties'][count_column]),
            'color': 'black',
            'weight': line_weight,
            'fillOpacity': 0.5,
        },
        tooltip=folium.features.GeoJsonTooltip(fields=[LSOA_column, count_column],
                                               aliases=['LSOA Code', 'IMD Quintile'],
                                               labels=True)
    ).add_to(m)

    # Render choropleth map if count column is provided
    #if count_column is not None:
    #    # Add choropleth layer
    #    folium.Choropleth(
    #        geo_data=gdf,
    #        data=gdf,
    #        columns=[gdf.index, count_column],
    #        key_on='feature.id',
    #        fill_color=color_scheme,  # Adjust color scheme
    #        fill_opacity=0.7,
    #        line_opacity=0.2,
    #        legend_name='Count'
    #    ).add_to(m)
    
    # Add the color scale legend
    color_scale.add_to(m)

    # Render the map in Streamlit using streamlit_folium
    #folium_static(m)#, width=400, height=750)
    folium_static(m, width=550, height=650)

    return m


#----------------------------------------------
@st.cache_data(ttl=1800)
def calculate_age_sum(df, min_age, max_age, lsoa_code_column):
    """
    Calculate the sum of columns between the specified age range for each row in the DataFrame.

    Parameters:
    - df (DataFrame): Source DataFrame containing age columns.
    - min_age (int): Minimum age to consider (inclusive).
    - max_age (int): Maximum age to consider (inclusive).

    Returns:
    - DataFrame: Updated DataFrame containing the LSOA code column and the sum of age columns.
    """
 # Convert age range to strings
    age_columns = [str(age) for age in range(min_age, max_age + 1)]

    # Sum the selected columns along the rows
    df['Age_Sum'] = df[age_columns].sum(axis=1)

    # Create a new DataFrame with LSOA code column and age sum
    result_df = df[[lsoa_code_column, 'Age_Sum']]

    return result_df

#----------------------------------------------
'''
def plot_geodata_with_basemap_ctx(gdf):
    """
    Plot GeoDataFrame with a background basemap from OpenStreetMap.

    Parameters:
    - gdf (GeoDataFrame): GeoDataFrame containing the geometries to plot.

    Returns:
    - None
    """
    # Set the CRS of the GeoDataFrame to EPSG 3857 (Web Mercator) for compatibility with contextily
    gdf = gdf.to_crs(epsg=3857)

    # Create a matplotlib figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot GeoDataFrame geometries
    gdf.plot(ax=ax, color='none', edgecolor='blue')

    # Add background map from OpenStreetMap
    ctx.add_basemap(ax, url=ctx.providers.OpenStreetMap.Mapnik)

    # Turn off axis
    ax.axis('off')

    # Set plot title
    plt.title('Geographical Data with OpenStreetMap Basemap')

    # Show plot in Streamlit
    st.pyplot(fig)
'''
#----------------------------------------------

def render_map_lsoa_in_area(local_authorities, lsoa_data):
    # Filter LSOA data based on the provided list of local authorities
    lsoa_data_filtered = lsoa_data[lsoa_data['LocalAuthority'].isin(local_authorities)]

    # Create a folium map centered on the mean coordinates of the filtered LSOAs
    m = folium.Map(location=[lsoa_data_filtered.centroid.y.mean(), lsoa_data_filtered.centroid.x.mean()], zoom_start=10)

    # Add LSOA boundaries to the map
    folium.GeoJson(lsoa_data_filtered,
                   tooltip=folium.GeoJsonTooltip(fields=['LSOA11NM'], localize=True),
                   ).add_to(m)

    return m

#----------------------------------------------

def main():
    st.title('LSOA Count Visualization')

    # Load shapefile data
    lsoa_data = load_shapefile('path_to_shapefile.shp')

    # Sidebar for user input
    st.sidebar.header('Input')
    local_authority = st.sidebar.selectbox('Select Local Authority', lsoa_data['LocalAuthority'].unique())

    # Render map
    st.header('Map')
    map_data = render_map(local_authority, count_data, lsoa_data)
    folium_static(map_data)

#----------------------------------------------

# Function to dynamically generate the list of years for the second selectbox
def get_remaining_years(options, selected_year):
    index = options.index(selected_year)  # Find the index of the selected year
    remaining_years = options[index+1:]   # Extract the remaining years
    return remaining_years

#----------------------------------------------

# Function to filter DataFrame based on user-provided arguments
@st.cache_data(ttl=1800)
def filter_dataframe_pop_projections(geography_level, dict_files, locations, start_year, end_year, gender, age_range):
    if geography_level == 'Upper Tier or Unitary Authority':
        df = dict_files['pop_projections']['pop_proj_utla']
        location = 'unitary or UTLA'
    elif geography_level == 'District Authority or Place':
        df = dict_files['pop_projections']['pop_proj_district']
        location = 'LA_district_or_unitary'
    else: 
        st.write(' -- Error in function -- ')
    
    # First stage of filtering: Filter rows based on locations
    location_mask = df[location].isin(locations)
    
    # Filter columns based on start and end years
    columns_to_keep = [location, 'Age_Range', 'Gender', str(start_year), str(end_year)]
    df = df[columns_to_keep]
    
    # Second stage of filtering: Apply the location mask
    df = df[location_mask]
    
    # Filter rows based on gender
    df = df[df['Gender'] == gender]
    
    # Filter rows based on age range
    if age_range != "All ages":
        df = df[df['Age_Range'] == age_range]
    else:
        # Sum population columns for all age ranges
        df = df.groupby([location, 'Gender']).sum().reset_index()
        df['Age_Range'] = 'All ages'
    
    # Calculate net difference between end_year and start_year
    df['Net_Difference'] = df[str(end_year)] - df[str(start_year)]
    
    # Calculate percentage change
    df['Percentage_Change'] = (df['Net_Difference'] / df[str(start_year)]) * 100
    
    df.rename(columns={location: 'Location'}, inplace=True)

    return df

#----------------------------------------------

def visualize_population_change(df):
    # Create Altair chart
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Location', title='Location'),
        y=alt.Y('Percentage_Change', title='% Population Change'),
        tooltip=['Location', 'Percentage_Change']
    ).properties(
        width=600,
        height=400,
        title='% Population Change by Location'
    ).interactive()

    # Display Altair chart in Streamlit
    st.write(chart)

#----------------------------------------------

# Function to filter DataFrame based on user-provided arguments
@st.cache_data(ttl=1800)
def filter_dataframe(data_dict, locations, start_year, end_year, gender, age_range):
    df = data_dict['df']
    
    # Filter rows based on locations
    df = df[df['Location'].isin(locations)]
    
    # Filter columns based on start and end years
    columns_to_keep = ['Location', 'Age_Range', 'Gender'] + [str(year) for year in range(start_year, end_year + 1)]
    df = df[columns_to_keep]
    
    # Filter rows based on gender
    df = df[df['Gender'] == gender]
    
    # Filter rows based on age range
    if age_range != "All ages":
        df = df[df['Age_Range'] == age_range]
    else:
        # Sum population columns for all age ranges
        df = df.groupby(['Location', 'Gender']).sum().reset_index()
        df['Age_Range'] = 'All ages'
    
    return df
#----------------------------------------------

@st.cache_data
def create_data_files(
    lookup_imd_decile,
    loookup_imd_decile_detailed,
    loookup_lsoa_to_utla,
    lookup_lsoa_lower_tier_la,
    pop_est_females_syoa,
    pop_est_males_syoa,
    pop_est_persons_syoa,
    shapefile_path_lsoa,
    #shapefile_path_utla,
    pop_proj_path_utla,
    pop_proj_path_district
    ):

    dict_data_files = {}

    #create dataframes from files at file paths above
    #look ups
    df_lookup_imd_decile = pd.read_csv(lookup_imd_decile)
    df_lookup_imd_decile_detailed = pd.read_csv(loookup_imd_decile_detailed)
    df_loookup_lsoa_to_utla = pd.read_csv(loookup_lsoa_to_utla)
    df_lookup_lsoa_lower_tier_la = pd.read_csv(lookup_lsoa_lower_tier_la)

    dict_lookups = {}
    dict_lookups['df_imd_decile'] = df_lookup_imd_decile
    dict_lookups['df_imd_decile_detailed'] = df_lookup_imd_decile_detailed
    dict_lookups['df_lsoa_to_utla'] = df_loookup_lsoa_to_utla
    dict_lookups['df_lsoa_lower_tier'] = df_lookup_lsoa_lower_tier_la

    #pop estimates
    df_pop_est_females_syoa = pd.read_csv(pop_est_females_syoa)
    df_pop_est_males_syoa = pd.read_csv(pop_est_males_syoa, nrows=34754, encoding='latin1') #encoding issue with utf - unsure why - latin encoding seems to work
    df_pop_est_persons_syoa = pd.read_csv(pop_est_persons_syoa)

    dict_pop_estimates = {}
    dict_pop_estimates['Female'] = df_pop_est_females_syoa
    dict_pop_estimates['Male'] = df_pop_est_males_syoa
    dict_pop_estimates['Persons'] = df_pop_est_persons_syoa

    #shapefiles
    gdf_lsoa = gpd.read_file(shapefile_path_lsoa)
    #gdf_utla = gpd.read_file(shapefile_path_utla)

    dict_shapefiles = {}
    dict_shapefiles['gdf_lsoa'] = gdf_lsoa
    #dict_shapefiles['gdf_utla'] = gdf_utla

    #pop projections
    dict_pop_projections = {}
    df_pop_proj_utla = pd.read_csv(pop_proj_path_utla)
    df_pop_proj_district = pd.read_csv(pop_proj_path_district)
    #update dict
    dict_pop_projections['pop_proj_utla'] = df_pop_proj_utla
    dict_pop_projections['pop_proj_district'] = df_pop_proj_district

    #master dictionary
    dict_files = {}
    dict_files['lookups'] = dict_lookups
    dict_files['pop_estimates'] = dict_pop_estimates
    dict_files['shapefiles'] = dict_shapefiles
    dict_files['pop_projections'] = dict_pop_projections

    return dict_files 

#----------------------------------------------
@st.cache_data(ttl=1800)
def convert_deciles_to_quintiles(df, imd_decile_col):
    """
    Convert decile values to quintile values, retaining rows with None in 'IMD Decile'.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing an 'IMD Decile' column with decile values.

    Returns:
    pd.DataFrame: Updated DataFrame with quintile values, including original None values.
    """
    # Create a new column for the quintiles
    # Using a lambda function to convert only non-None values
    quintiles  = df[imd_decile_col].apply(lambda x: ((x - 1) // 2) + 1 if pd.notnull(x) else None)

    # Find the index of the IMD Decile column
    decile_col_index = df.columns.get_loc(imd_decile_col)

    # Insert the quintile values right after the IMD Decile column
    df.insert(loc=decile_col_index + 1, column='IMD Quintile', value=quintiles)

    return df



#----------------------------------------------



#----------------------------------------------



#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
#----------------------------------------------
