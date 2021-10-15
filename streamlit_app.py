import streamlit as st

from functions import (get_infection_data,
                       get_prevalence,
                       get_pydeck_chart,
                       )

st.set_page_config(page_title='Slovakia risk assessment',
                   page_icon='favicon.ico',
                   layout="wide")

cases, start_date, end_date = get_infection_data()

st.title("""
    Slovakia event risk assessment: probability of having an infected person
""")
st.markdown(f"""
    Based on 7-day infection data
    between **{start_date}**
    and **{end_date}**.
""")

st.sidebar.title("Parameters")
ascertainment_bias = st.sidebar.slider(
    "Ascertainment bias",
    min_value=1,
    max_value=10,
    value=5,
    format="%dx",
)
nr_of_people = st.sidebar.slider(
    "Event size",
    min_value=1,
    max_value=250,
    value=50,
)

st.sidebar.markdown(
    """
        ### Estimation logic :spiral_note_pad:
        Covid-19 prevalence is estimated based on product of the 7-day
        incidence rate and the ascertainment bias.
        The 7-day incidence rate is the same measure
        as the government uses for assessing Covid-19 dynamics.
        The ascertainment bias (measuring the ratio of unreported cases)
         has not been estimated in Berlin yet.
        However, based on other estimates on seroprevalence,
        it usually lies between 5 and 10.

        Assuming completely random mixing at event,
        the probability of having an infected person is then
        $1-(1-p)^n$, where $p$ denotes the prevalence and $n$ the event size.

        #### Data source :file_cabinet:
        [PCR tests]
        (https://github.com/Institut-Zdravotnych-Analyz/covid19-data/tree/main/PCR_Tests)

        [Antibody tests]
        (https://github.com/Institut-Zdravotnych-Analyz/covid19-data/tree/main/AG_Tests)
        
        [Demographics]
        (http://statdat.statistics.sk/)

        #### Acknowledgements :wave:
        This tool has taken inspirations from
        [COVID-19 Event Risk Assessment Planning Tool]
        (https://covid19risk.biosci.gatech.edu/).
    """, )

st.sidebar.markdown(
    """
        #### Licence
        <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
        <img alt="Creative Commons Licence" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png" />
        </a>
        <br />This work is licensed under a
        <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
        Creative Commons Attribution-NonCommercial 4.0 International License</a>.
    """,
    unsafe_allow_html=True,
)

prevalence = get_prevalence(cases, ascertainment_bias)

st.pydeck_chart(get_pydeck_chart(prevalence, nr_of_people))
