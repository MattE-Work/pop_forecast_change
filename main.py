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
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

#import modules
from pages.page_functions import file_upload_warnings as warn

#--------------------------------------------------------------
st.title(':rainbow[Population Forecast Change]')
st.header(':violet[About:]')
st.write("""This app has been built in an attempt to combine separate data sources 
into a single, usable format, to help planning for potential future population change.
""")
st.write('Please review the expanders below for more information.')

with st.expander(':violet[**Purpose**]'):
    with st.container(border=True):
        #st.subheader('Purpose:')
        st.write("""This app has been built to combine several publicly available 
        data sources with the intention of aiding understanding of anticipated population 
        change over time.""")
with st.expander(':violet[**How to use this app**]'):
    #st.subheader('How to use this app:')
    st.write("""Use the menu to the left 👈🏻 to access the different pages. Each 
    page provides different functionality. For example use the: 
    \n***high level pop change*** page to access anticipated population change by a given cohort of the population. This page also allows you to run this process for multiple services/contexts concurrently via a file upload; or
    \n***mapping pop change*** page to visualise population change geographically and support operational considerations.
    """)
with st.expander(':violet[**Is it accurate?**]'):
    #st.subheader('So, is it accurate?')
    st.write("""For the avoidance of doubt, it ***cannot*** be ***accurate***. It is intended as a 
    tool to leverage available data sources and provide insight based on those 
    and a small number of assumptions in the methods applied. For this reason, 
    the output can be considered ***indicative***.""")
with st.expander(':violet[**Methods**]'):
    #st.subheader('What assumptions are made?')
    st.write("""An overview of the method applied / assumptions made is provided 
    on each page.""")
with st.expander(':violet[**⚠️Data use reminder and license information⚠️**]'):
    #st.subheader('Licence information')
    st.write("""This app has been produced under an MIT license. It may change over time and without warning.""")
    warn.general_warning()