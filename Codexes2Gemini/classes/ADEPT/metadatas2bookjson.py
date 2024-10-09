#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import json
import os

import pandas as pd
import streamlit as st

from app.utilities.metadatas2outputformats import metadatas2bookjson

thisdoc_dir = "output/ADA470697"
st.write(thisdoc_dir)
with st.status("creating cover metadata"):
    try:
        st.info('trying')
        if os.path.exists(f"{thisdoc_dir}/metadatas.json"):
            # read df from json
            with open(f"{thisdoc_dir}/metadatas.json", "r") as f:
                metadatas_dict = json.load(f)
                st.write(metadatas_dict)
                metadatas_df = pd.DataFrame(metadatas_dict)
                st.write(metadatas_df)
    except Exception as e:
        st.error(e)
        st.error("no metadatas.json file found, aborting")
        st.stop()
    bookjson = metadatas2bookjson(metadatas_df, thisdoc_dir)
