import streamlit as st
import pandas as pd
import altair as alt
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from streamlit_folium import st_folium

#import modules
from pages.page_functions import pop_data_ETL_functions as pop_ETL
from pages.page_functions import map_functions as map_func
from pages.page_functions import file_upload_warnings as warn

#set page config
st.set_page_config(layout="wide")

#----------------------------
#Title
#----------------------------
st.title(':green[Mapping Population Forecast Change]🗺️')
debug_mode = st.radio(label='turn on debug mode', options=['Yes', 'No'], index=1, horizontal=True, help='Turning this on will display the tables that are produced when the model runs. The formatting of these is not great, it has largely been included to aid with putting this together, but kept in case you want to visualise the method being applied.')
#----------------------------
#Overview of functionality (summary) - signpost to menu to review the method 
#and assumptions that are being made in the model
#----------------------------
st.header(':red[Read this👇🏻first!]👨🏻‍⚖️')

with st.expander(label='**:red[Click for overview of this page]**'):
    #license and data sources
    license_url = 'https://github.com/MattE-Work/pop_forecast_change/blob/main/LICENSE'
    license_html = f'<a href="{license_url}" target="_blank">License terms.</a>'
    
    st.subheader('License terms:')
    st.write('This resource is provided under an MIT license. It is your responsibility to familiarise yourself with and abide by the terms of this license, via the link below:')
    st.markdown(license_html, unsafe_allow_html=True)
    
    st.subheader('Reference data sources:')
    st.write('The reference data used in this app is all publicy available from the below sources (links working as of May 2024).')
    
    ons_lsoa_syoa_sex_url = 'https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates'
    ons_lsoa_syoa_sex_html = f'<a href="{ons_lsoa_syoa_sex_url}" target="_blank">ONS - 2022 LSOA by single year of age and sex</a>'
    
    lsoa_imd_open_communities_url = 'https://opendatacommunities.org/resource?uri=http%3A%2F%2Fopendatacommunities.org%2Fdata%2Fsocietal-wellbeing%2Fimd2019%2Findices'
    lsoa_imd_open_communities_html = f'<a href="{lsoa_imd_open_communities_url}" target="_blank">Department for Levelling Up Housing and Communities - 2019 IMD by LSOA</a>'

    nomis_url = 'https://www.nomisweb.co.uk/sources'
    nomis_html = f'<a href="{nomis_url}" target="_blank">NOMIS Official Census and Labour Market Statistics - population forecasts by single year of age and gender</a>'

    #st.write("**Links to sources below (links working as of May 2024):**")
    st.markdown(ons_lsoa_syoa_sex_html, unsafe_allow_html=True)
    st.markdown(lsoa_imd_open_communities_html, unsafe_allow_html=True)
    st.markdown(nomis_html, unsafe_allow_html=True)

    st.subheader('Method overview:')
    st.write("""
        \n1 - The baseline population for each individual age in the age range, gender, and baseline year is retrieved at LSOA level. 
        \n2 - The baseline and forecast population for the specified populatoin is retrieved at the selected higher level geography (district / UTLA)
        \n3 - The net and percentage change is derived at the higher level geography and for each individual age range in the range for each area in the selected geography/ies
        \n4 - Because forecast population data is not available at LSOA level, the model applies the higher level percentage change by age range to all LSOAs that fall within that higher level geography (assumes all LSOA population change is consistent within the given area)
        \n5 - The net change at LSOA level is derived, this is used in the map of population change.
        \n6 - The baseline and forecast prevalence rate are applied to the relevant population, the net change between the two is then derived.
    """)






#----------------------------
#Set global variables
#----------------------------
local_authorities = [
    "Derby", "Derbyshire"
    ] 

districts = [
    'Amber Valley',
    'Bolsover',
    'Chesterfield',
    'Derby',
    'Derbyshire Dales',
    'Erewash',
    'High Peak',
    'North East Derbyshire',
    'South Derbyshire',
]

default_option = '---'

#list options for modelling future demand
prevalence_use = 'Use crude prevalence rates'
apply_population_change = 'Apply population change to current demand'

#list options for baseline demand setting
baseline_demand_apportion_total_activity = 'Enter a total activity figure'
baseline_demand_upload_lsoa_aggregate_counts = 'Upload a file of agregated activity counts by LSOA'

#POP FORECASTS
pop_proj_path_utla = r'build_data/pop_projections/utla_pop_forecast_24_to_43_jucd_only.csv'
pop_proj_path_district = r'build_data/pop_projections/district_pop_forecast_24_to_43_jucd_only.csv'

#IMD DECILE BY LSOA
lsoa_imd_decile_path = r'build_data/lsoa_imd_decile/lsoa_imd_decile.csv'
df_lsoa_imd_decile = pd.read_csv(lsoa_imd_decile_path)

#call function to create dict of necessary reference files
df_pop_forecast_district = pd.read_csv(pop_proj_path_district)
df_pop_forecast_utla = pd.read_csv(pop_proj_path_utla)

list_possible_ages = list(df_pop_forecast_district.iloc[:,2:-2].columns)
list_possible_years = list(set(list(df_pop_forecast_district['Year'])))

#list_possible_district_las = sorted(list(set(df_pop_forecast_district['local authority'])))
#list_possible_utlas = sorted(list(set(df_pop_forecast_utla['local authority'])))

#load the shapefile
#geodf_lsoa_boundaries = map_func.load_shapefile(r'build_data/shapefiles/LSOA_2021_EW_BFC_V8.shp')
geodf_lsoa_boundaries = map_func.load_shapefile(r'build_data/shapefiles_subset/local_area_shapefile.shp')

#----------------------------
#Parameter selection within expander to save screen space from results
#----------------------------
st.header(':green[Set parameters]')

with st.expander('Click to view / set required parameters'):
#with st.form(key='params_form'):
    #district(s) the service operates out of

    #col1, col2 = st.columns(2)
    #with col1:
    geography_level = st.selectbox(
        'Select the level of geography to map', 
        options=['Upper Tier or Unitary Authority', 'District Authority or Place'], 
        index=1)

    #done
    if geography_level == 'Upper Tier or Unitary Authority':
        area_text = "Upper Tier or Unitary Authority/ies"
        list_options = local_authorities
        df_forecast_pop_all_years = df_pop_forecast_utla
        default_options = ['Derbyshire', 'Derby']

    #TODO
    elif geography_level == 'District Authority or Place':
        area_text = "Place(s) or District Authority/ies"
        list_options = districts
        default_options = ['Amber Valley', 'Bolsover', 'Chesterfield', 'Derbyshire Dales', 'Erewash', 'High Peak', 'North East Derbyshire', 'South Derbyshire', 'Derby']
        df_forecast_pop_all_years = df_pop_forecast_district
    else:
        st.write('invalid selection')

    #with col1:
    list_of_areas_to_forecast = st.multiselect(
        f'Select the {area_text} you want to forecast for', 
        options=list_options,
        default=default_options
        )


    #min age range of the service
    col1, col2, col3 = st.columns(3)
    with col1:
        options_ages_with_default = [default_option]
        options_ages_with_default+=list_possible_ages

        pop_proj_min_age = st.selectbox(
                    label='Select the minimum age range under consideration', 
                    options=options_ages_with_default)

    #max age range of the service
    with col2:
        remaining_options_ages = pop_ETL.get_remaining_years(options_ages_with_default, pop_proj_min_age)
        
        remaining_options_ages_with_default = [default_option]
        remaining_options_ages_with_default+=remaining_options_ages
        
        pop_proj_max_age = st.selectbox(
            label='Select the maximum age range under consideration', 
            options=remaining_options_ages_with_default)

    #pop service sees 
    with col3:
        pop_proj_gender = st.selectbox(label='Select the gender for the population forecast', options=[default_option, 'Persons', 'Males', 'Females'])


    #Setting baseline and forecast year
    col1, col2 = st.columns(2)
    #baseline year for population estimate
    with col1:
        options_years_with_default = [default_option]
        options_years_with_default+=list_possible_years

        pop_proj_baseline_year = st.selectbox(
            label='Select baseline year', 
            options=options_years_with_default,
            index=1, 
            #disabled=True
            )
    #future forecast year for population estimate
    with col2:
        remaining_options = pop_ETL.get_remaining_years(options_years_with_default, pop_proj_baseline_year)
        remaining_options_years_with_default = [default_option]
        remaining_options_years_with_default+=remaining_options

        pop_proj_forecast_year = st.selectbox(
            label='Select forecast year', 
            options=remaining_options_years_with_default,
            index=0)

    #Decide how to model future demand
    how_to_model_demand = st.selectbox(
        label='How do you want to model future demand?',
        options=[default_option, prevalence_use, apply_population_change], index=1, disabled=True) #Current only allows prevalence option

    #if apportioning activity, number input for the current number of contacts in a given time period
    if how_to_model_demand == prevalence_use:
        col1, col2 = st.columns(2)
        #baseline prevalence
        with col1:
            baseline_prevalence = st.number_input(
                label=f'Baseline prevalence per 100k pop. in {pop_proj_baseline_year}'
            )
        #future prevalence
        with col2:
            forecast_prevalence = st.number_input(
                label=f'Forecast prevalence per 100k pop. in {pop_proj_forecast_year}'
            )
    else:
        pass
    

    #Decide how to enter baseline demand level (load data or apportion a single demand figure)
    #how to model future demand - either applying population change, or, prevalence rates
    how_to_enter_baseline_demand = st.selectbox(
        label='How do you want to enter baseline demand?',
        options=[default_option, baseline_demand_apportion_total_activity, baseline_demand_upload_lsoa_aggregate_counts],
        index=1,disabled=True
        )

    #enter activity total to apportion to all LSOAs based on pop size per LSOA
    # NOTE: this approach cannot be accurate, render warnings in read me and when produced !!
    if how_to_enter_baseline_demand == baseline_demand_apportion_total_activity:
        total_activity_number = st.number_input(
            label='Enter the demand number for the service/condition you are modelling:',
            help='This could be the unique number of patients referred in a year (regardless whether this resulted in an attendance), if you wanted to consider "expressed need", for example.')
    
    #if selected load data, render render file upload option
    elif how_to_enter_baseline_demand == baseline_demand_upload_lsoa_aggregate_counts:
        warn.render_warning_lsoa_count_for_map()

        df_path = st.file_uploader(label='Select the file containing **only** aggregate counts per LSOA')
        if df_path == None and debug_mode == 'No':
            st.stop()
        elif df_path != None and debug_mode == 'No':
            df_users_activity_per_lsoa = pd.read_csv(df_path)
            
            col1, col2 = st.columns(2)
            with col1:
                lsoa_col = st.selectbox(label='Select the LSOA 2021 Code column', options=df_users_activity_per_lsoa.columns)
            with col2:
                activity_count_col = st.selectbox(label='Select the column containing activity counts', options=df_users_activity_per_lsoa.columns)
                total_activity_number = df_users_activity_per_lsoa[activity_count_col].sum()

        elif df_path == None and debug_mode == 'Yes':
            st.write('Dummy data in use')

    st.subheader(':green[Select outputs to produce]')
    col1, col2 = st.columns(2)
    with col1:
        list_type_of_outputs = st.multiselect(label='Select the type of outputs you want to produce', options=['Maps', 'Charts'])
    with col2:
        list_possible_outputs = []
        if 'Maps' in list_type_of_outputs:
            list_possible_outputs += ['Map - Deprivation (IMD)', 'Map - Population Change', 'Map - Estimated Need Change']
            if how_to_enter_baseline_demand == baseline_demand_upload_lsoa_aggregate_counts:
                list_possible_outputs+=['Map - Current demand vs Need']
        if 'Charts' in list_type_of_outputs:
            list_possible_outputs += ['Chart - Population Change', 'Chart - Modelled Demand Change']
        list_outputs = st.multiselect(label='Select the outputs to produce', options=list_possible_outputs)

#button_confirm_params = st.button(label='Confirm parameters')
#if not button_confirm_params:
#    st.stop()
#else:
#    pass


#Use the parameters to derive the required datasets
try:
    df_lsoa_syoa_selected_age_range = pop_ETL.load_and_process_baseline_data(pop_proj_gender, geography_level, list_of_areas_to_forecast, pop_proj_min_age, pop_proj_max_age)
except:
    st.stop()

#function call to derive the total pop in the age / gender of interest
df_summed_pop_change = pop_ETL.forecast_population(
        df_forecast_pop_all_years,
        list_of_areas_to_forecast,
        pop_proj_min_age,
        pop_proj_max_age,
        pop_proj_baseline_year,
        pop_proj_forecast_year,
        pop_proj_gender
        )


#calculate the population change percentage for the chosen geography, age, gender, timeframes
df_individual_ages_pop_change = pop_ETL.forecast_population_by_age(
    df_forecast_pop_all_years, 
    list_of_areas_to_forecast, 
    pop_proj_min_age, 
    pop_proj_max_age, 
    pop_proj_baseline_year, 
    pop_proj_forecast_year, 
    pop_proj_gender
    )

#aggregated up the above df, to sum pop for each year of age by each geography in scope
#df_aggregated_change_by_year_of_age = pop_ETL.aggregate_by_age(df_individual_ages_pop_change)

#apply the pop change above to the LSOAs, that fall within the geography selected
df_inflated_lsoa_level_pop = pop_ETL.apply_percent_changes_iteratively(df_lsoa_syoa_selected_age_range, df_individual_ages_pop_change, geography_level)


#<<< testing section >>>>
#st.write('debug section')
#st.write(baseline_lsoa_pop_syoa_filtered_subset_cols)
#-------------------------------

if debug_mode == 'Yes':
    st.header('Susbet baseline pop by single year of age and district selections')
    st.write(df_lsoa_syoa_selected_age_range.head())
    st.write('source forecast df for single year of age, selected geography, available genders')
    st.write(df_forecast_pop_all_years.head())
    st.write('sum pop change at the selected geography, gender, and age range')
    st.write(df_summed_pop_change)
    st.header('pop change at the selected geography, gender, for each individual age in the chosen age range')
    st.write(df_individual_ages_pop_change)
    #st.write('aggregated up the above df, to sum pop for each year of age by each geography in scope')
    #st.write(df_aggregated_change_by_year_of_age)
    st.write('apply the pop change above to the LSOAs, that fall within the geography selected')
    st.write(df_inflated_lsoa_level_pop)


#filtering large shapefile to local lsoas only so can upload to git using GUI
#st.write(geodf_lsoa_boundaries)
#list_local_lsoas = list(df_inflated_lsoa_level_pop['LSOA21CD'])
## Filter the GeoDataFrame
#local_area_gdf = geodf_lsoa_boundaries[geodf_lsoa_boundaries['LSOA21CD'].isin(list_local_lsoas)]
#local_area_gdf.to_file('build_data/shapefiles_subset/local_area_shapefile.shp')

#----------------------------
#merge with df created above with the shapefile loaded into variable geodf_lsoa_boundaries
#when the app loaded (this is held in cache after that point)
#----------------------------
if how_to_model_demand == prevalence_use:
    #apply prevalence rates to 
    df_inflated_lsoa_level_pop = pop_ETL.calculate_and_insert_needs(df_inflated_lsoa_level_pop, baseline_prevalence, forecast_prevalence)
    #st.write(df_inflated_lsoa_level_pop)

else:
    #consider incorporating here logic to increase demand figure by pop change % ? 
    pass


#merge in IMD decile to ensure this is in the geodf (next line)
df_inflated_lsoa_level_pop = pop_ETL.merge_imd_decile(df_inflated_lsoa_level_pop, df_lsoa_imd_decile)

#convert imd deciles to quintiles
df_inflated_lsoa_level_pop = map_func.convert_deciles_to_quintiles(df_inflated_lsoa_level_pop, 'IMD Decile')

# Merge the GeoDataFrame with the count data DataFrame
gdf_merged = geodf_lsoa_boundaries.merge(df_inflated_lsoa_level_pop, on='LSOA21CD', how='inner')

#list_test_to_map = ['LSOA21CD', 'geometry', 'Baseline Population']


#map = map_func.render_folium_map_heatmap_net_change(gdf_merged, 'Net Pop Change', line_weight=1, title='')

#----------------------------
#Map section using two tabs
#Tab 1: 3 maps side by side using 3 columns
    #Map 1: IMD by LSOA (as is) - static map renders on load?
    #Map 2: AS IS population size by LSOA for selected sex/age range
    #Map 3: FORECAST population size by LSOA for selected sex/age range

#Tab 2: 2 demand maps side by side
    #Map 4: demand by LSOA AS IS (either using upload file, or, apportioned demand) - timing when to render needs error control logic
    #Map 5: demand by LSOA MODELLED FUTURE

    
    #Map 6: 

#----------------------------
#prep
#derive centroid of the selected districts, *should* ensure the maps are rendered centrally in the folium plots

#----------------------------------------

# Rendering selected outputs in tabs
if list_outputs:
    st.header(':green[Outputs:]')
    tabs = st.tabs([output.split(" - ")[1] for output in list_outputs])
    for i, tab in enumerate(tabs):
        with tab:
            #map_func.render_output(list_outputs[i])
            if list_outputs[i] == 'Map - Deprivation (IMD)':
                st.subheader('Map of deprivation (IMD)')
                st.write("""The below map shows deprivation quintiles, with areas more 
                deprived shaded in red, and areas less deprived shaded in green.""")
                imd_decile_map = map_func.render_folium_map_heatmap(gdf_merged, count_column='IMD Quintile', line_weight=1, color_scheme='RdYlGn', title='', LSOA_column = 'LSOA21CD')
            
            elif list_outputs[i] == 'Map - Population Change':
                st.subheader(f'Map of Population Change ({pop_proj_gender}, aged {pop_proj_min_age}-{pop_proj_max_age})')
                st.write('The below map shows modelled population change in the demographic of interest. Population decreases are shaded :blue[**blue**] and population increases are shaded :red[**red**].')
                map = map_func.render_folium_map_heatmap_net_change(gdf_merged, 'Net Pop Change', line_weight=1, title='')
            
            elif list_outputs[i] == 'Map - Estimated Need Change':
                st.subheader(f'Map of Estimated Change in Need ({pop_proj_gender}, aged {pop_proj_min_age}-{pop_proj_max_age})')
                st.write('The below map shows modelled change in need, using the user entered prevalence rates, and applying these to the estimated future population. Decreases are shaded :blue[blue] and increases are shaded :red[red].')
                map = map_func.render_folium_map_heatmap_net_change(gdf_merged, 'Net Need Change', line_weight=1, title='')
            
            elif list_outputs[i] == 'Chart - Population Change':
                st.write('This section still needs to be built.')
            
            elif list_outputs[i] == 'Map - Current demand vs Need':
                st.subheader(f'Map of Baseline Estimated Need Seen ({pop_proj_gender}, aged {pop_proj_min_age}-{pop_proj_max_age})')
                st.write("""The below map shows the difference between estimated 
                need at LSOA level and the volume of demand presenting to the 
                service. 
                \nValues in :blue[**blue**] indicate areas where expressed need is 
                greater than anticipated need. Conversely, areas in :red[**red**] 
                indicate areas where the volume of activity seen is less than 
                the level of estimated need in that area, based on the entered prevalence rate.""")
                
                user_df = df_users_activity_per_lsoa[[lsoa_col, activity_count_col]]
                gdf_subset_baseline_met_need = gdf_merged[['LSOA21CD', 'geometry', 'Baseline Need']]

                # Merge the GeoDataFrame with the DataFrame
                gdf_subset_baseline_met_need = gdf_subset_baseline_met_need.merge(user_df, on=lsoa_col, how='left')

                # Fill missing Activity_Count values with 0
                gdf_subset_baseline_met_need[activity_count_col] = gdf_subset_baseline_met_need[activity_count_col].fillna(0)

                # Calculate 'Baseline Met Need'
                gdf_subset_baseline_met_need['Baseline Met Need'] = gdf_subset_baseline_met_need['Baseline Need'] - gdf_subset_baseline_met_need[activity_count_col]

                #st.write(gdf_subset_baseline_met_need.head())
                map = map_func.render_folium_map_heatmap_net_change(gdf_subset_baseline_met_need, 'Baseline Met Need', line_weight=1, title='')

            elif list_outputs[i] == 'Chart - Modelled Demand Change':
                st.header('Demand considerations')

                #derive metrics
                sum_baseline_need = df_inflated_lsoa_level_pop['Baseline Need'].sum()
                sum_forecast_need = df_inflated_lsoa_level_pop['Forecast Need'].sum()
                overall_percent_change = (sum_forecast_need - sum_baseline_need) / sum_baseline_need
                
                if debug_mode == 'Yes':
                    st.write(sum_baseline_need)
                    st.write(sum_forecast_need)
                    st.write(overall_percent_change)

                st.subheader('Proportion of baseline need presenting as demand')
                st.write(f'The service sees {round(((total_activity_number/sum_baseline_need)*100),2)}% of the modelled baseline need.')
                
                st.subheader('Future demand')
                forecast_demand = total_activity_number + (total_activity_number * overall_percent_change)

                st.write(f"""Assuming this % remains constant, based on population change 
                and any change to the prevalence rate, future demand in {pop_proj_forecast_year} could be in the order of 
                {round(forecast_demand,2)}. This represents a change of :red[**{round((forecast_demand - total_activity_number),0)}**]""")

                #st.write(f'This presents a change of :red[**{round((forecast_demand - total_activity_number),0)}**]')
                
                #balance number to adjusted when changing modifiers
                forecast_demand_modified = round((forecast_demand - total_activity_number),0)
                forecast_demand_baseline = round((forecast_demand - total_activity_number),0)

                
                st.header('Demand Modifier Considerations')
                
                st.write('The below is intended to aid planning, by considering system 4 considerations for modifying future demand increases (where applicable / possible).')
                col1, col2, col3 = st.columns(3)
                with col1: 
                    #Technology
                    tech_modified_slider = st.slider(label='Technology', min_value=-100, max_value=100, value=0)
                    #Environmental
                    environmental_modified_slider = st.slider(label='Environmental', min_value=-100, max_value=100, value=0)
                    #Economic
                    economic_modified_slider = st.slider(label='Economic', min_value=-100, max_value=100, value=0)
            
                with col2:
                    #Social
                    social_modified_slider = st.slider(label='Social', min_value=-100, max_value=100, value=0)
                    #Political
                    political_modified_slider = st.slider(label='Political', min_value=-100, max_value=100, value=0)
                    #Educational
                    educational_modified_slider = st.slider(label='Educational', min_value=-100, max_value=100, value=0)

                with col3:
                    #Ecological
                    ecological_modified_slider = st.slider(label='Ecological', min_value=-100, max_value=100, value=0)
                    #Commercial
                    commercial_modified_slider = st.slider(label='Commercial', min_value=-100, max_value=100, value=0)
                    #Legal
                    legal_modified_slider = st.slider(label='Legal', min_value=-100, max_value=100, value=0)
                
                list_modifiers = [
                    tech_modified_slider,
                    environmental_modified_slider,
                    economic_modified_slider,
                    social_modified_slider,
                    political_modified_slider,
                    educational_modified_slider,
                    ecological_modified_slider,
                    commercial_modified_slider,
                    legal_modified_slider,
                ]

                net_reduction_value = sum([(modifier / 100) * forecast_demand_baseline for modifier in list_modifiers])
                forecast_demand_modified += net_reduction_value
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader('Modified demand net increase:')
                with col2:
                    if forecast_demand_modified > 0:
                        st.subheader(f":red[{round(forecast_demand_modified,0)}]")
                    else:
                        st.subheader(f":green[{round(forecast_demand_modified,0)}]")

                #Technology
                #Environmental
                #Economic
                #Social
                #Political
                #Educational
                #Ecological
                #Commercial
                #Demograpghic #Excluded, as this is the purpose of the tool. 
                #Legal


#----------------------------------------

#tabs = st.tabs(['Deprivation (IMD)', 'Map of population change', 'Map of estimated need change', 'Modelled demand change'])

#tab 1 - deprivation 
#with tabs[0]:
#    #Map 1: IMD by LSOA (as is) - static map renders on load?
#    st.subheader('Map of deprivation (IMD)')
#    st.write('The below map shows deprivation quintiles, with areas more deprived shaded in red, and areas less deprived shaded in green.')
#    #imd_decile_map = map_func.render_folium_map_heatmap(gdf_merged, count_column='IMD Quintile', line_weight=1, color_scheme='RdYlGn', title='', LSOA_column = 'LSOA21CD')
#    imd_decile_map = map_func.render_folium_map_heatmap(gdf_merged, count_column='IMD Quintile', line_weight=1, color_scheme='RdYlGn', title='', LSOA_column = 'LSOA21CD')
#
##tab 2 - population net change map
#with tabs[1]:
#    st.subheader(f'Map of Population Change ({pop_proj_gender}, aged {pop_proj_min_age}-{pop_proj_max_age})')
#    st.write('The below map shows modelled population change in the demographic of interest. Population decreases are shaded :blue[blue] and population increases are shaded :red[red].')
#    map = map_func.render_folium_map_heatmap_net_change(gdf_merged, 'Net Pop Change', line_weight=1, title='')
#
##tab 3 - estimated need chart (renders net change)
#with tabs[2]:
#    st.subheader(f'Map of Estimated Change in Need ({pop_proj_gender}, aged {pop_proj_min_age}-{pop_proj_max_age})')
#    st.write('The below map shows modelled change in need, using the user entered prevalence rates, and applying these to the estimated future population. Decreases are shaded :blue[blue] and increases are shaded :red[red].')
#    map = map_func.render_folium_map_heatmap_net_change(gdf_merged, 'Net Need Change', line_weight=1, title='')
#    
##tab 4 - demand now and future
#with tabs[3]:
#    st.header('Demand considerations')
#
#    #derive metrics
#    sum_baseline_need = df_inflated_lsoa_level_pop['Baseline Need'].sum()
#    sum_forecast_need = df_inflated_lsoa_level_pop['Forecast Need'].sum()
#    overall_percent_change = (sum_forecast_need - sum_baseline_need) / sum_baseline_need
#    
#    if debug_mode == 'Yes':
#        st.write(sum_baseline_need)
#        st.write(sum_forecast_need)
#        st.write(overall_percent_change)
#
#    st.subheader('Proportion of baseline need presenting to service as demand')
#    st.write(f'The service sees {round(((total_activity_number/sum_baseline_need)*100),2)}% of the modelled baseline need.')
#    
#    st.subheader('Future demand')
#    forecast_demand = total_activity_number + (total_activity_number * overall_percent_change)
#
#    st.write(f"""Assuming this % remains constant, based on population change 
#    and any change to the prevalence rate, future demand in {pop_proj_forecast_year} could be in the order of 
#    {round(forecast_demand,2)}""")
#
#    st.write(f'This presents a change of :red[**{round((forecast_demand - total_activity_number),0)}**]')
    
    #baseline_demand_as_proporton_of_need = total_activity_number
    #baseline_demand_as_proporton_of_need = total_activity_number / 
    #map_baseline_pop = map_func.render_folium_map_heatmap(gdf_merged, count_column='Baseline Population', line_weight=1, color_scheme='YlOrRd', title=f'{pop_proj_baseline_year} population', LSOA_column='LSOA21CD', scale=scale)
    
    

    

    



#Method - varies depending on modelling method selected
#step 1 - get the relevant current population
#load derby / derbyshire LSOA by single year of age and sex data sets
#filter to the age range / sex selected by user
#Ensure there are LSOA code and District name fields in the df
#Filter the df to the selected district(s) the user has selected

#step 2 
#POPULATION CHANGE METHOD:
#overview: get the % change between baseline and forecast year, for each age within the age range, inclusive
# - load nomis population forecast datasets
# - subset to the sex / age range / district(s) according to user inputs
# - calculate the % change figure for each age in the range (inclusive) for each district selected
# - subset the lsoa population baseline df, to have a subset df for each district in scope. Do the same for the forecast pop df (so we have 2 lots of subset dfs, a baseline and forecast pop per district)
# - loop through the subset baseline population dfs, for each, matrix multiply by the percent change for that district
# - join all subsets with the forecast pop figure back together

#ALTERNATIVE - USING 2 PREVALENCE RATES METHOD
#overview: apply the 2 prevalence rates to the respective population at each time point
# - 


#step 3 - apply the percentage change to the baseline population number for each age for each LSOA
#?? matrix multiplication an option here


#step 4 - render the map in column 3


#----------------------------
#display the forecast future activity figure
#----------------------------
