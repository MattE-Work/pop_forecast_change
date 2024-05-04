#import geopandas as gpd
import pandas as pd
import streamlit as st
#import folium
#from folium.plugins import MarkerCluster
#import matplotlib.pyplot as plt
#from streamlit_folium import st_folium
import altair as alt


#import functions
#import pages.page_functions.map_functions as map_func

#set page config
st.set_page_config(layout="wide")

#import modules
from pages.page_functions import file_upload_warnings as warn


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

    #result_df.reset_index(inplace=True)
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

    #shortened_service_df = shortened_service_df.reset_index(inplace=True)

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

#list_possible_district_las = sorted(list(set(df_pop_forecast_district['local authority'])))
#list_possible_utlas = sorted(list(set(df_pop_forecast_utla['local authority'])))
#--------------------------------------------------------------
#--------------------------------------------------------------

#create shape file variable from dictionary
#gdf_lsoa = dict_files['shapefiles']['gdf_lsoa']

st.title(':blue[Population Forecast Change]')
st.subheader('Read me: (functionality and data sources)')
with st.expander(label='Click for overview of data sources'):
    #local_authorities = [
    #"Derby", "Derbyshire", "Leicester", "Leicestershire", "Lincolnshire", 
    #"Northamptonshire", "Nottingham", "Nottinghamshire", "Rutland",
    #"Barnsley", "Doncaster", "Rotherham", "Sheffield"
    #] 
    
    st.write('The data used in this app is all publicy available from NOMIS web (population projections)')
    st.write('https://www.nomisweb.co.uk/')
with st.expander('Assumptions, caveats, and method information'): 
    st.write('1. This :red[***does not***] consider whether  :red[***current***] demand is appropriate.')
    st.write('2. The population data used was from a 2018 forecast (therefore 2024 is also a :red[***forecast***] figure)')
    st.write('3. The same prevalence rates are applied to future years unless indicated. This is because. while we know prevalence will change for risk factors / conditions, we do not have this information available for all risk factors in a standard form/for each forecast year.')
    st.write('4. Net cost demand change simply multiplies future demand by the average unit cost today.')
    st.write("""5. Population change is derived by summing the populaton between min 
    nd max age inclusive, for the selected gender, for both baseline and forecast year, then 
    deriving the net and percentage change between the two.""")


#--------------------------------------------------------------

st.subheader('How do you want to use this tool?')

#col1, col2 = st.columns(2)
#with col1:
use_case = st.selectbox(label='Select how you want to use this tool:', options=['For just one service', 'For many services (requires file upload)'])

#--------------------------------------------------------------

if use_case == 'For just one service':
    with st.expander(label='Click to enter parameters'):
        st.subheader('Set up parameters')

        options_ages = list_possible_ages
        col1, col2, col3 = st.columns(3)
        with col1: 
            pop_proj_gender = st.selectbox(label='Select the gender for the population forecast', options=['Persons', 'Male', 'Female'])
        with col2:
            pop_proj_min_age = st.selectbox(
                label='Select the minimum age range under consideration', 
                options=options_ages)
        with col3:
            remaining_options_ages = get_remaining_years(options_ages, pop_proj_min_age)
            pop_proj_max_age = st.selectbox(
                label='Select the maximum age range under consideration', 
                options=remaining_options_ages)

        
        geography_level = st.selectbox(
            'Select the level of geography to map', 
            options=['Upper Tier or Unitary Authority', 'District Authority or Place'], 
            index=0)

        #done
        if geography_level == 'Upper Tier or Unitary Authority':
            area_text = "Upper Tier or Unitary Authority/ies"
            list_options = ['Derbyshire', 'Derby']
            pop_df = df_pop_forecast_utla
            default_options = ['Derbyshire', 'Derby']

        #TODO
        elif geography_level == 'District Authority or Place':
            area_text = "Place(s) or District Authority/ies"
            list_options = ['Amber Valley', 'Bolsover', 'Chesterfield', 'Derbyshire Dales', 'Erewash', 'High Peak', 'North East Derbyshire', 'South Derbyshire', 'Derby']
            default_options = ['Amber Valley', 'Bolsover', 'Chesterfield', 'Derbyshire Dales', 'Erewash', 'High Peak', 'North East Derbyshire', 'South Derbyshire', 'Derby']
            pop_df = df_pop_forecast_district
        else:
            st.write('invalid selection')

        list_of_areas_to_forecast = st.multiselect(
            f'Select the {area_text} you want to forecast for', 
            options=list_options,
            default=default_options
            )

        options = list_possible_years
        col1, col2 = st.columns(2)
        with col1:
            
            pop_proj_baseline_year = st.selectbox(
                label='Select baseline year', 
                options=options,
                index=0)

        with col2:
            remaining_options = get_remaining_years(options, pop_proj_baseline_year)
            pop_proj_forecast_year = st.selectbox(
                label='Select forecast year', 
                options=remaining_options,
                index=0)
        
        
        

        st.subheader('Refinements')
        col1, col2 = st.columns(2)
        with col1:
            apply_known_prevalence_to_service = st.selectbox(label='Would you like to apply a known prevalence rate for your service?', options=['Yes', 'No'], index=1)
        if apply_known_prevalence_to_service == 'Yes':
            with col1:
                baseline_model_prevalence = st.slider(label='Baseline prevalence of service demand / condition', min_value=0.1, max_value=100.0, step=0.1)
                forecast_model_prevalence = st.slider(label='Forecast prevalence of service demand / condition', min_value=0.1, max_value=100.0, step=0.1)
        with col2:
            model_modifiable_risk_factor = st.selectbox(label='Would you like to also quantify prevalence of modifiable risk factor in your service demand (E.g. number smoking etc.)?', options=['Yes', 'No'], index=1)
            if model_modifiable_risk_factor == 'Yes':
                with col2:
                    baseline_mod_risk_factor_prevalence = st.slider(label='Baseline prevalence of modifiable risk factor', min_value=0.1, max_value=100.0, step=0.1)
                    forecase_mod_risk_factor_prevalence = st.slider(label='Forecast prevalence of modifiable risk factor', min_value=0.1, max_value=100.0, step=0.1)
        
    try:
        st.header('Outputs:')
        st.subheader('Population change in selected areas:')
        
        df_single_service_pop_change = forecast_population(
        pop_df,
        list_of_areas_to_forecast,
        pop_proj_min_age,
        pop_proj_max_age,
        pop_proj_baseline_year,
        pop_proj_forecast_year,
        pop_proj_gender
        )

        #if prevalence or risk factor used, update the df with this information
        if apply_known_prevalence_to_service == 'Yes':
            df_single_service_pop_change['Baseline prevalence'] = round(df_single_service_pop_change['Baseline Year Total'] * (baseline_model_prevalence / 100),1)
            df_single_service_pop_change['Forecast prevalence'] = round(df_single_service_pop_change['Forecast Year Total'] * (forecast_model_prevalence / 100),1)
        if model_modifiable_risk_factor == 'Yes':
            df_single_service_pop_change['Baseline mod risk factor'] = round(df_single_service_pop_change['Baseline Year Total'] * (baseline_mod_risk_factor_prevalence / 100),1)
            df_single_service_pop_change['Forecast mod risk factor'] = round(df_single_service_pop_change['Forecast Year Total'] * (forecase_mod_risk_factor_prevalence / 100),1)
                
        #col1, col2 = st.columns(2)
        #with col1:
        st.dataframe(df_single_service_pop_change.iloc[:,1:])
        #with col2:
        
            
    except:
        st.stop()
    

    #st.write(df_single_service_pop_change)
    y_variable = st.selectbox('What would you like to display on the chart?', options=df_single_service_pop_change.columns, index=1) 
    
    bar_chart = create_bar_chart(df_single_service_pop_change, y_variable, x_variable='Location')
    st.altair_chart(bar_chart)


#--------------------------------------------------------------

elif use_case == 'For many services (requires file upload)':
    pop_df = df_pop_forecast_district
    #upload file section
    #with col2:
    warn.render_warning_service_coverage()

    users_file = st.file_uploader(
        label='Select the file to upload',
        accept_multiple_files=False
    )

    if users_file == None:
        use_dummy_data = st.radio(
            label='No file uploaded. Do you want to use dummy data to preview functionality?', 
            options=['Yes', 'No'],
            index=1,
            horizontal=True)
        if use_dummy_data == 'No':
            st.stop()
        #users_file = 'zTestData\\dummy_data_service_age_coverage.csv'
        users_file = r'zTestData/dummy_data_service_age_coverage_with_WTE.csv'
        st.write('Test/dummy data in use as no file selected')
    
    service_df = pd.read_csv(users_file)
    st.subheader('Preview of data set in use:')
    with st.expander(label='Click to preview the dataset in use:'):
        st.dataframe(service_df)

    st.subheader('Set parameters:')
    options = list_possible_years
    col1, col2 = st.columns(2)
    with col1:
        
        pop_proj_baseline_year = st.selectbox(
            label='Select baseline year', 
            options=options,
            index=0)

    with col2:
        remaining_options = get_remaining_years(options, pop_proj_baseline_year)
        pop_proj_forecast_year = st.selectbox(
            label='Select forecast year', 
            options=remaining_options,
            index=0)

    #with col3:
    #        chart_metric = st.selectbox(
    #            'What do you want to chart?',
    #            options = [
    #                'Net Pop Change', 
    #                '% Pop Change', 
    #                'Net Est Demand Change',
    #                'Net Cost Demand Change (£1000s)'
    #                ])
    

    col1, col2, col3 = st.columns(3)
    with col1:
        smoking_prevalence = st.slider(label='Est. smoking prevalence', min_value=0.0, max_value=100.0, value=13.2, step=0.1)
    with col2:
        overweight_or_obesity_prevalence = st.slider(label='Est. overweight or obesity prevalence', min_value=0.0, max_value=100.0, value=64.0, step=0.1)
    with col3:
        obesity_prevalence = st.slider(label='Est. obesity prevalence', min_value=0.0, max_value=100.0, value=26.0, step=0.1)

    
    st.subheader('Population change by service:')
    updated_service_df_with_pop_demand_forecast, shortened_service_df_with_forecast = calculate_population_changes(service_df, pop_df, pop_proj_baseline_year, pop_proj_forecast_year)
    
    #update shortened_service_df_with_forecast with modifiable risk factor population using user-provided prevalence rate, for the current attendances
    shortened_service_df_with_forecast['Current est smokers'] = round((shortened_service_df_with_forecast['Forecasted Demand'] - shortened_service_df_with_forecast['Net Est Demand Change']) * (smoking_prevalence/100),0)
    shortened_service_df_with_forecast['Current est overweight or obese pts'] = round((shortened_service_df_with_forecast['Forecasted Demand'] - shortened_service_df_with_forecast['Net Est Demand Change']) * (overweight_or_obesity_prevalence/100),0)
    shortened_service_df_with_forecast['Current est obese pts'] = round((shortened_service_df_with_forecast['Forecasted Demand'] - shortened_service_df_with_forecast['Net Est Demand Change']) * (obesity_prevalence/100),0)
    
    #update shortened_service_df_with_forecast with modifiable risk factor population using user-provided prevalence rate for the forecast demand population
    shortened_service_df_with_forecast['Forecast est smokers'] = round(shortened_service_df_with_forecast['Forecasted Demand'] * (smoking_prevalence/100),0)
    shortened_service_df_with_forecast['Forecast est overweight or obese pts'] = round(shortened_service_df_with_forecast['Forecasted Demand'] * (overweight_or_obesity_prevalence/100),0)
    shortened_service_df_with_forecast['Forecast est obese pts'] = round(shortened_service_df_with_forecast['Forecasted Demand'] * (obesity_prevalence/100),0)

    with st.expander(label='Click to preview the updated dataset with forecasts added'):
        st.write(updated_service_df_with_pop_demand_forecast) 

    #col1, col2 = st.columns(2)

    #with col1:
    st.write(shortened_service_df_with_forecast) 
    #with col2:
    #    st.altair_chart(create_population_change_chart_service_upload(shortened_service_df_with_forecast, chart_metric, pop_proj_baseline_year, pop_proj_forecast_year))
    
    st.subheader('Chart maker')
    st.write('Use the selection options below to visualise the outputs:')
    col1, col2, col3 = st.columns(3)
    with col1:
        chart_type = st.selectbox('Select chart type', options=['bar chart', 'scatter chart'])
    with col2:
        x_variable = st.selectbox('Select the X variable', options=shortened_service_df_with_forecast.columns, index=1)    
    if chart_type == 'scatter chart':
        with col3:
            y_variable = st.selectbox('Select the Y variable', options=shortened_service_df_with_forecast.columns, index=5)    
    
    
    if chart_type == 'scatter chart':
        scatter_plot = create_scatter_chart(shortened_service_df_with_forecast, x_variable, y_variable, 1200, 400)
        st.altair_chart(scatter_plot, use_container_width=True)
    elif chart_type == 'bar chart':
        bar_chart = create_bar_chart(shortened_service_df_with_forecast, x_variable)
        st.altair_chart(bar_chart)

    #test print statements - looks to be working / calculating pop summed figures correctly
    #test_list_las = ['Derby'] #needs to be derived from the service df for the given row, where the row has 'yes' in the column for district
    #test_la_df = pop_df[pop_df['local authority'].isin(test_list_las)] 
    #test_la_df_baseline = test_la_df[test_la_df['Year'] == 2042] #replace 2024 with the baseline_year (function argument)
    #test_la_df_baseline_gender = test_la_df_baseline[test_la_df_baseline['Gender'] == 'Female'] #replace Persons with service_gender (function argument)
    #test_la_df_baseline_gender_year_range = test_la_df_baseline_gender.loc[:,'18':'45'] #should reflect min age : max age in .loc column selection
    #st.write(test_la_df_baseline_gender_year_range)
    #st.write(test_la_df_baseline_gender_year_range.sum().sum())

    