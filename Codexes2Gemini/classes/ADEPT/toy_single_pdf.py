import os

import streamlit as st
import shutil

st.info('first line')
st.info(os.getcwd())
# from classes.ADEPT.SinglePDFProcessor import SinglePDFProcess as spdf
from classes.ADEPT.ADEPT_utilities import ADEPT_utilities as au
# Create a SinglePDFProcess object
# This object will be used to process a single PDF
# from app.utilities.utilities import smart_print
from classes.Codexes.Metadata import Metadatas

sp = spdf('9781934840122_spacewars.pdf', 'working/contracted/active_copyedit')
st.write(sp)
st.info("hello")
st.info(sp.filepath)
st.info(os.getcwd())

# parts = PartsOfTheBook()

# metadatas = main(sp)
