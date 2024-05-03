
import streamlit as st
import altair as alt
import pandas as pd
import geopandas as gpd

#--------------------------------------------------------------
# define functions
#--------------------------------------------------------------

# Function to dynamically generate the list of years for the second selectbox
def get_remaining_years(options, selected_year):
    index = options.index(selected_year)  # Find the index of the selected year
    remaining_years = options[index+1:]   # Extract the remaining years
    return remaining_years

def forecast_population(pop_df, local_authorities, min_age, max_age, start_year, forecast_year, gender):

    # Filter data for the specified local authorities
    df_filtered = pop_df[pop_df['local authority'].isin(local_authorities)]
    
    # Filter data for the specified gender
    df_filtered = df_filtered[df_filtered['Gender'] == gender]
    # Define age columns to sum based on min_age and max_age
    age_columns = [str(age) for age in range(int(min_age), int(max_age) + 1)]
    
    # Filter and calculate for the start_year
    baseline_data = df_filtered[df_filtered['Year'] == start_year]
    baseline_pop = baseline_data[age_columns].sum(axis=1)
   
    baseline_total = baseline_pop.groupby(baseline_data['local authority']).sum()
    
    # Filter and calculate for the forecast_year
    forecast_data = df_filtered[df_filtered['Year'] == forecast_year]
    forecast_pop = forecast_data[age_columns].sum(axis=1)
    forecast_total = forecast_pop.groupby(forecast_data['local authority']).sum()

    # Calculate net change and percentage change
    net_change = forecast_total - baseline_total
    percent_change = (net_change / baseline_total) * 100
    
    # Prepare the final DataFrame for output (working code on individual service use case)
    result_df = pd.DataFrame({
        'Location': local_authorities,
        f'Total Pop Age {min_age}-{max_age} ({gender})': baseline_total,
        'Baseline Year Total': baseline_total,
        'Forecast Year Total': forecast_total,
        'Net Change': net_change,
        '% Change': percent_change
    })

    return result_df


def create_population_change_chart(df, chart_metric):
    """
    This function creates an Altair chart object for rendering in Streamlit, showing either the net change
    or the percentage change in population for different locations based on the 'chart_metric' parameter.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing 'Location', 'Net Change', and 'Percentage Change' columns.
    chart_metric (str): Column name to chart ('Net Change' or 'Percentage Change').
    
    Returns:
    alt.Chart: An Altair chart object for rendering.
    """
    # Validate input
    assert chart_metric in ['Net Change', '% Change'], "chart_metric must be 'Net Change' or 'Percentage Change'."
    assert 'Location' in df.columns and chart_metric in df.columns, "DataFrame must include 'Location' and specified chart_metric columns."

    # Define the color condition based on the selected metric
    color_condition = alt.condition(
        alt.datum[chart_metric] > 0,
        alt.value("steelblue"),  # Positive changes in blue
        alt.value("red")  # Negative changes in red
    )
    
    # Create the chart
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Location:N', sort='-y', title='Local Authority'),
        y=alt.Y(f'{chart_metric}:Q', title=f'{chart_metric} by Local Authority'),
        color=color_condition,
        tooltip=['Location', alt.Tooltip(f'{chart_metric}:Q', title=chart_metric)]  # Reflects the selected metric
    ).properties(
        width=600,
        height=400,
        title=f'{chart_metric} by Local Authority'
    )

    return chart


def create_population_change_chart_service_upload(df, chart_metric, pop_proj_baseline_year, pop_proj_forecast_year):
    """
    This function creates an Altair chart object for rendering in Streamlit, showing either the net change
    or the percentage change in population for different locations based on the 'chart_metric' parameter.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing 'Location', 'Net Change', and 'Percentage Change' columns.
    chart_metric (str): Column name to chart ('Net Change' or 'Percentage Change').
    
    Returns:
    alt.Chart: An Altair chart object for rendering.
    """
    # Validate input
    assert chart_metric in ['Net Pop Change', '% Pop Change', 'Net Est Demand Change', 'Net Cost Demand Change (£1000s)'], "chart_metric must be 'Net Change' or 'Percentage Change'."
    assert 'Service name' in df.columns and chart_metric in df.columns, "DataFrame must include 'Location' and specified chart_metric columns."

    # Define the color condition based on the selected metric
    color_condition = alt.condition(
        alt.datum[chart_metric] > 0,
        alt.value("steelblue"),  # Positive changes in blue
        alt.value("red")  # Negative changes in red
    )
    
    # Create the chart
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Service name:N', sort='-y', title='Service'),
        y=alt.Y(f'{chart_metric}:Q', title=f'{chart_metric}'),
        color=color_condition,
        tooltip=['Service name', alt.Tooltip(f'{chart_metric}:Q', title=chart_metric)]  # Reflects the selected metric
    ).properties(
        width=600,
        height=400,
        title=f'{chart_metric} by Service between {str(pop_proj_baseline_year)} and {str(pop_proj_forecast_year)}'
    )

    return chart


def get_population_for_service(pop_df, local_authorities, min_age, max_age, baseline_year, forecast_year, gender):
    # Filter the population dataframe for the specified local authorities
    la_df = pop_df[pop_df['local authority'].isin(local_authorities)]
    
    # Get the baseline population
    baseline_df = la_df[(la_df['Year'] == baseline_year) & (la_df['Gender'] == gender)]
    age_columns = [str(age) for age in range(min_age, max_age + 1)]
    baseline_population = baseline_df[age_columns].sum().sum()

    # Get the forecast population
    forecast_df = la_df[(la_df['Year'] == forecast_year) & (la_df['Gender'] == gender)]
    forecast_population = forecast_df[age_columns].sum().sum()

    return baseline_population, forecast_population

# Example usage in Streamlit app
def calculate_population_changes(service_df, pop_df, baseline_year, forecast_year):
    # Assuming all columns after the 4th index are local authorities
    local_authorities_columns = service_df.columns[6:]

    # Initialize new columns for the output
    service_df['Baseline Population'] = 0
    service_df['Forecast Population'] = 0
    service_df['Net Pop Change'] = 0
    service_df['% Pop Change'] = 0.0
    service_df['Forecasted Demand'] = 0
    service_df['Net Est Demand Change'] = 0
    service_df['Net Cost Demand Change (£1000s)'] = 0
    service_df['attendances per wte'] = 0

    for index, service_row in service_df.iterrows():
        # Identify which local authorities are marked as 'yes'
        selected_local_authorities = [la for la in local_authorities_columns if service_row[la] == 'yes']
        
        # Call the function to get populations
        baseline_population, forecast_population = get_population_for_service(
            pop_df,
            selected_local_authorities,
            service_row['min age seen'],
            service_row['max age seen'],
            baseline_year,
            forecast_year,
            service_row['gender seen']
        )

        # Calculate net change and percent change
        net_change = forecast_population - baseline_population
        percent_change = (net_change / baseline_population * 100) if baseline_population else 0

        # Calculate the forecasted demand by applying the percentage change to the attendances
        forecasted_demand = round(service_row['attendances in 12 months'] * (1 + (percent_change / 100)),0)
        net_change_forecast_demand = forecasted_demand - service_row['attendances in 12 months']
        cost_demand_change = (net_change_forecast_demand * (service_row['average cost per appt'])) / 1000

        #calculate the average number of attendances per wte
        attends_per_wte = service_row['attendances in 12 months'] / service_row['clinical_wte'] 

        # Update the service dataframe with the calculated populations
        service_df.at[index, 'Baseline Population'] = baseline_population
        service_df.at[index, 'Forecast Population'] = forecast_population
        service_df.at[index, 'Net Pop Change'] = net_change
        service_df.at[index, '% Pop Change'] = percent_change
        service_df.at[index, 'Forecasted Demand'] = forecasted_demand
        service_df.at[index, 'Net Est Demand Change'] = net_change_forecast_demand
        service_df.at[index, 'Net Cost Demand Change (£1000s)'] = cost_demand_change
        service_df.at[index, 'attendances per wte'] = attends_per_wte

    # Now create a new dataframe with only the required columns
    columns_to_keep = [service_df.columns[0]] + service_df.columns[-5:].tolist()
    shortened_service_df = service_df[columns_to_keep]

    return service_df, shortened_service_df


def create_scatter_chart(df, x_variable, y_variable, width, height):
    """
    Render a scatter chart using Altair with given x and y variables.

    Parameters:
    df (pd.DataFrame): The data frame containing the data.
    x_variable (str): The column name to be used for the x-axis.
    y_variable (str): The column name to be used for the y-axis.

    Returns:
    alt.Chart: An Altair Chart object that can be rendered in Streamlit.
    """
    # Calculate the max values for each axis and add 1
    x_max = df[x_variable].max() + 1
    x_min = df[x_variable].min() - 1
    y_max = df[y_variable].max() + 1
    y_min = df[y_variable].min() - 1

    chart = alt.Chart(df).mark_point().encode(
        x=alt.X(x_variable, scale=alt.Scale(domain=(x_min, x_max))),
        y=alt.Y(y_variable, scale=alt.Scale(domain=(y_min, y_max))),
        tooltip=['Service name',x_variable, y_variable]
    ).properties(width=width, height=height).interactive()
    return chart


def create_bar_chart(df, y_variable, x_variable='Service name'):
    """
    Render a bar chart using Altair with the given x variable and a specified y variable.
    Bars are colored based on their value being positive (steel blue) or negative (red).

    Parameters:
    df (pd.DataFrame): The data frame containing the data.
    x_variable (str): The column name to be used for the x-axis, which represents the categories.
    y_variable (str): The column name to be used for the y-axis, which represents the values.

    Returns:
    alt.Chart: An Altair Chart object that can be rendered in Streamlit.
    """
    sorted_df = df.sort_values(by=y_variable, ascending=False)

    chart = alt.Chart(sorted_df).mark_bar().encode(
        x=alt.X(x_variable, title=x_variable, sort=alt.EncodingSortField(field=y_variable, order='descending')),  # Category axis
        y=alt.Y(y_variable, title=y_variable),  # Value axis
        color=alt.condition(
            alt.datum[y_variable] >= 0,  # Condition for deciding color based on the y value
            alt.value("steelblue"),  # True color (positive values)
            alt.value("red")  # False color (negative values)
        ),
        tooltip=[x_variable, alt.Tooltip(y_variable, title='Value')]
    ).properties(
        width=600,
        height=400,
        title=f'Distribution of {x_variable}'
    ).interactive()

    return chart

#--------------------------------------------------------------
#load required files
#--------------------------------------------------------------

#POP FORECASTS
pop_proj_path_utla = r'build_data/pop_projections/pop_forecast_24_to_43.csv'
pop_proj_path_district = r'build_data/pop_projections/district_pop_forecast_24_to_43.csv'

#--------------------------------------------------------------
#Make dataframes
#--------------------------------------------------------------

#call function to create dict of necessary reference files
df_pop_forecast_district = pd.read_csv(pop_proj_path_district)
df_pop_forecast_utla = pd.read_csv(pop_proj_path_utla)

#get possible single years of age in the forecast pop df
list_possible_ages = list(df_pop_forecast_district.iloc[:,2:-2].columns)
list_possible_years = list(set(list(df_pop_forecast_district['Year'])))

list_possible_district_las = sorted(list(set(df_pop_forecast_district['local authority'])))
list_possible_utlas = sorted(list(set(df_pop_forecast_utla['local authority'])))


#--------------------------------------------------------------
#load and subset the lsoa and single year of age baseline population
#--------------------------------------------------------------
def load_and_process_baseline_data(pop_proj_gender, geography_level, list_of_areas_to_forecast, pop_proj_min_age, pop_proj_max_age):
    # Determine file path based on gender selection
    file_path = f"build_data/baseline_pop_lsoa_syoa_sex/2022_{pop_proj_gender.lower()}_lsoa_syoa.csv"
    baseline_lsoa_pop_syoa = pd.read_csv(file_path)
    
    # Load the LSOA to district and UTLA lookup file and clean it
    lsoa_district_utla_lookup = pd.read_csv('build_data/lookups/lsoa_2021_to_la_district.csv')
    lsoa_district_utla_lookup.drop(['ObjectId', 'utla_name'], axis=1, inplace=True)


    # Determine the column to filter on based on user parameter selected
    filter_column = 'LA Name' if geography_level == 'Upper Tier or Unitary Authority' else 'LAD23NM'

    # Merge LA districts into the syoa lsoa pop to allow filtering in next stage
    baseline_lsoa_pop_syoa_updated = baseline_lsoa_pop_syoa.merge(
        lsoa_district_utla_lookup, left_on='LSOA 2021 Code', right_on='LSOA21CD', how='left')

    # Subset to the selected geography/ies
    baseline_lsoa_pop_syoa_filtered = baseline_lsoa_pop_syoa_updated[
        baseline_lsoa_pop_syoa_updated[filter_column].isin(list_of_areas_to_forecast)]


    # Find the index position where age columns start and calculate index positions for the age range
    age_start_col_index = int(baseline_lsoa_pop_syoa_filtered.columns.get_loc('0'))  # Assuming '0' is the first age column
    min_col_index = age_start_col_index + int(pop_proj_min_age)
    max_col_index = age_start_col_index + int(pop_proj_max_age) + 1

    filter_col_index = baseline_lsoa_pop_syoa_filtered.columns.get_loc(filter_column)

    # Select all rows, the third column (LSOA code), and the age range columns
    baseline_lsoa_pop_syoa_filtered_subset_cols = baseline_lsoa_pop_syoa_filtered.iloc[
        :, [2, filter_col_index] + list(range(min_col_index, max_col_index))]


    # Summing rows from column index 2 to the last column
    baseline_lsoa_pop_syoa_filtered_subset_cols['Baseline Population'] = baseline_lsoa_pop_syoa_filtered_subset_cols.iloc[:, 2:].sum(axis=1)

    # Insert the new column at index position 1
    # This requires creating a new DataFrame or adjusting the columns
    column_order = baseline_lsoa_pop_syoa_filtered_subset_cols.columns.tolist()
    # Move 'Total Population' to the second position (index 1)
    new_columns = [column_order[0], 'Baseline Population'] + column_order[1:-1]
    baseline_lsoa_pop_syoa_filtered_subset_cols = baseline_lsoa_pop_syoa_filtered_subset_cols[new_columns]

    return baseline_lsoa_pop_syoa_filtered_subset_cols

#----------------------------------
#apply pop change % between year X and Y, at selected geography
#to the LSOAs within that selected geography
#----------------------------------
def apply_percent_changes_iteratively(df_lsoa_level, df_higher_level_pop_change, geography_level):
    # Load DataFrames
    lsoa_counts_df = df_lsoa_level.copy(deep=True)
    #percent_changes_df = df_higher_level_pop_change

    # Iterate over each location and age in the percent_changes DataFrame
    for _, change_row in df_higher_level_pop_change.iterrows():
        location = change_row['Location']
        age = str(change_row['Age'])  # Ensuring age is a string if your column names are strings
        percent_change = change_row['% Change'] / 100.0

        # Check if the age column exists in lsoa_counts_df to avoid KeyErrors
        if age in lsoa_counts_df.columns:
            # Construct the mask for rows where the LSOA code matches
            if geography_level == 'District Authority or Place':
                mask = lsoa_counts_df['LAD23NM'] == location
            elif geography_level == 'Upper Tier or Unitary Authority':
                mask = lsoa_counts_df['LA Name'] == location
            else:
                pass

            # Apply the percent change to the population count for the matching rows and age column
            # Ensure that operation is only performed where mask is True
            lsoa_counts_df.loc[mask, age] = lsoa_counts_df.loc[mask, age] * (1 + percent_change)

    # Summing rows from column index 2 to the last column
    lsoa_counts_df['Forecast Population'] = lsoa_counts_df.iloc[:, 3:].sum(axis=1)
    #add net change column
    #lsoa_counts_df['Net pop. change'] = lsoa_counts_df['Forecast Population'] - lsoa_counts_df['Baseline Population']
    #st.subheader('test df')
    #st.write(lsoa_counts_df)

    # Insert the new column at index position 1
    # This requires creating a new DataFrame or adjusting the columns
    column_order = lsoa_counts_df.columns.tolist()
    # Move 'Total Population' to the second position (index 1)
    new_columns = [column_order[0], column_order[1], 'Forecast Population'] + column_order[2:-1]
    lsoa_counts_df = lsoa_counts_df[new_columns]

    lsoa_counts_df.rename(columns={'LSOA 2021 Code': 'LSOA21CD'}, inplace=True)
    
    #calculate the net pop change
    difference = lsoa_counts_df['Baseline Population'] - lsoa_counts_df['Forecast Population']
    
    #insert the net pop change into the df
    lsoa_counts_df.insert(3, 'Net Pop Change', difference)

    return lsoa_counts_df

#-----------------------------------
#Calculate population metrics for each age within a specified range for given local authorities
#-----------------------------------

def forecast_population_by_age(pop_df, local_authorities, min_age, max_age, start_year, forecast_year, gender):
    """
    Calculate population metrics for each age within a specified range for given local authorities.

    Parameters:
    pop_df (DataFrame): The population DataFrame.
    local_authorities (list): List of local authorities to include.
    min_age (int): Minimum age in the range.
    max_age (int): Maximum age in the range.
    start_year (int): Baseline year for population data.
    forecast_year (int): Future year for population forecast.
    gender (str): Gender filter ('Male', 'Female', 'Persons').

    Returns:
    DataFrame: A DataFrame with population metrics by age for each local authority.
    """

    # Filter data for the specified local authorities and gender
    df_filtered = pop_df[(pop_df['local authority'].isin(local_authorities)) & (pop_df['Gender'] == gender)]

    # Initialize a list to hold data for the final DataFrame
    results = []

    # Iterate over each age in the specified range
    for age in range(int(min_age), int(max_age) + 1):
        age_column = str(age)

        # Filter and calculate for the baseline year
        baseline_data = df_filtered[df_filtered['Year'] == start_year]
        baseline_pop = baseline_data[age_column].groupby(baseline_data['local authority']).sum()

        # Filter and calculate for the forecast year
        forecast_data = df_filtered[df_filtered['Year'] == forecast_year]
        forecast_pop = forecast_data[age_column].groupby(forecast_data['local authority']).sum()

        # Calculate net change and percentage change
        net_change = forecast_pop - baseline_pop
        percent_change = (net_change / baseline_pop * 100).fillna(0)  # Handle division by zero

        # Store results for each age
        for location in local_authorities:
            results.append({
                'Location': location,
                'Age': age,
                'Baseline Population': baseline_pop.get(location, 0),
                'Forecast Population': forecast_pop.get(location, 0),
                'Net Change': net_change.get(location, 0),
                '% Change': percent_change.get(location, 0)
            })

    # Create a DataFrame from the results
    result_df = pd.DataFrame(results)

    return result_df

#------------------------------------------

def aggregate_by_age(df):
    # Group by 'Age' and sum the 'Baseline Population' and 'Forecast Population'
    aggregated_df = df.groupby('Age').agg({
        'Baseline Population': 'sum',
        'Forecast Population': 'sum'
    }).reset_index()

    # Calculate 'Net Change'
    aggregated_df['Net Change'] = aggregated_df['Forecast Population'] - aggregated_df['Baseline Population']

    # Calculate 'Percentage Change', handle division by zero where Baseline Population is zero
    aggregated_df['Percentage Change'] = aggregated_df.apply(
        lambda row: ((row['Net Change'] / row['Baseline Population']) * 100) if row['Baseline Population'] != 0 else 0, axis=1
    )

    return aggregated_df

#------------------------------------------

def calculate_and_insert_needs(df, baseline_prevalence, forecast_prevalence):
    """
    Applies given prevalence rates to population counts and inserts the results as new columns.
    
    Parameters:
    df (DataFrame): DataFrame containing LSOA21CD, Baseline Population, Forecast Population.
    baseline_prevalence (float): Baseline prevalence rate per 100,000.
    forecast_prevalence (float): Forecast prevalence rate per 100,000.
    """
    # Calculate baseline need
    # Convert prevalence per 100,000 to a proportion for calculation
    df['Baseline Need'] = (df['Baseline Population'] * (baseline_prevalence / 100000)).astype(int)
    
    # Insert the Baseline Need right after the Baseline Population
    # position 2 means it will be the third column (0-indexed)
    df.insert(loc=2, column='Baseline Need', value=df.pop('Baseline Need'))
    
    # Calculate forecast need
    df['Forecast Need'] = (df['Forecast Population'] * (forecast_prevalence / 100000)).astype(int)
    
    # Insert the Forecast Need right after the Forecast Population
    # position 4 means it will be the fifth column (0-indexed)
    df.insert(loc=4, column='Forecast Need', value=df.pop('Forecast Need'))

    # Calculate net need change (Forecast Need - Baseline Need)
    df['Net Need Change'] = df['Forecast Need'] - df['Baseline Need']
    # Insert the Net Need Change column after the Forecast Need
    df.insert(loc=5, column='Net Need Change', value=df.pop('Net Need Change'))

    return df

#------------------------------------------


def merge_imd_decile(df, df_lsoa_imd_decile):
    """
    Merges IMD decile data into the main DataFrame and inserts the new column at a specified position.
    
    Parameters:
    df (DataFrame): The main DataFrame containing LSOA21CD, Baseline Population, Forecast Population, etc.
    df_lsoa_imd_decile (DataFrame): DataFrame containing IMD deciles for each LSOA.
    
    Returns:
    DataFrame: Updated DataFrame with IMD Decile inserted.
    """
    # Merge IMD decile data
    merged_df = df.merge(df_lsoa_imd_decile[['FeatureCode', 'Value']], left_on='LSOA21CD', right_on='FeatureCode', how='left')

    # Drop the 'FeatureCode' column as it's redundant after merging
    merged_df.drop(columns='FeatureCode', inplace=True)

    # Rename 'Value' to 'IMD Decile'
    merged_df.rename(columns={'Value': 'IMD Decile'}, inplace=True)

    # Insert 'IMD Decile' column at position 1 (index 1)
    merged_df.insert(loc=1, column='IMD Decile', value=merged_df.pop('IMD Decile'))

    return merged_df

#------------------------------------------