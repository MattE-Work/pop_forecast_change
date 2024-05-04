import streamlit as st
import pandas as pd
import numpy as np

def render_warning_lsoa_count_for_map():
    st.subheader(':red[Warning!]⚠️')
    st.write(""":red[It is **your** responsibility to ensure the file you use 
    contains **only** aggregate counts of activity per LSOA, and **no other data**. 
    In choosing this option you are confirming you are doing so in accordance 
    with your organisation's Information Governance policies and all legal duties. 
    ]""")
    st.write(""":red[An example illustrating the required structure / content of the file is 
    provided below for your reference.]""")
    
    with st.container():
        # Seed for reproducibility
        np.random.seed(42)

        # Example LSOA codes for Derbyshire (these are hypothetical)
        lsoa_codes = [f'E0000000{i}' for i in range(1, 4)]

        # Generate random activity counts between 25 and 100
        activity_counts = np.random.randint(25, 101, size=3)

        # Create the DataFrame
        df = pd.DataFrame({
            'LSOA code': lsoa_codes,
            'Activity Count': activity_counts
        })

        # Append a new row with both columns set to 'etc.'
        df.loc[len(df)] = ['etc.', 'etc.']
        
        st.dataframe(df)


def render_warning_service_coverage():
    st.subheader(':red[Warning!]⚠️')
    st.write(""":red[It is **your** responsibility to ensure the file you use 
    contains **only** the required summary information per service (e.g. service name, 
    min age seen, max age seen, gender seen, and geographical coverage indicated by 
    'yes' or 'no') and **no other data**. In choosing this option you are 
    confirming you are doing so in accordance with your organisation's Information 
    Governance policies and all legal duties. 
    ]""")
    st.write(""":red[An example illustrating the required structure / content of the file is 
    provided below for your reference.]""")


def general_warning():
    st.subheader(':red[Warning!]⚠️')
    st.write(""":red[When using this app, if you choose to use the functonality 
    that requires an **aggregated** file to be uploaded, it is **your** responsibility 
    to ensure the file you use contains **only** the required summary information 
    and **no other data**. In choosing the option to use uploaded data you are 
    confirming you are doing so in accordance with your organisation's Information 
    Governance policies and all legal duties. 
    ]""")
    st.write(""":red[An example illustrating the required structure / content of 
    the file is provided in the app for your reference to ensure you use the correct 
    format.]""")