#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import logging
import os
import sys
import traceback

from mitosheet.streamlit.v1 import spreadsheet

from Codexes2Gemini.classes.Utilities.utilities import configure_logger

# print("Codexes2Gemini location:", Codexes2Gemini.__file__)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from Codexes2Gemini.classes.Codexes.CodexPeopleRoles.LeoBloom.leo_bloom_core import FinancialReportingObjects as FROs
from Codexes2Gemini.classes.Codexes.CodexPeopleRoles.LeoBloom.leo_bloom_core.FinancialReportingObjects import \
    Actual_Payment_History, AllUnitSalesThruToday, EstimatedUnpaidCompensation, FinancialReportingObjects, \
    FullMetadataEnhanced, FullMetadataIngest, LifetimePaidCompensation, LSI_Royalties_Due, LSI_Year_Data, \
    LSI_LTD_Paid_And_Unpaid_Compensation, LSI_Years_Data, ThisMonthUnitSales

import streamlit as st



def run_streamlit_app():
    report_classes = [Actual_Payment_History,

                      AllUnitSalesThruToday,
                      EstimatedUnpaidCompensation,
                      FinancialReportingObjects,
                      FullMetadataEnhanced,
                      FullMetadataIngest,
                      LifetimePaidCompensation,
                      LSI_LTD_Paid_And_Unpaid_Compensation,
                      LSI_Royalties_Due,
                      LSI_Year_Data,
                      LSI_Years_Data,

                      ThisMonthUnitSales]


    FRO = FROs.FinancialReportingObjects()
    dataframe_sections = {}  # Dictionary to store section names and positions

    for i, report_class in enumerate(report_classes):
        try:
            report_instance = report_class(FRO)
        except Exception as e:
            logging.error(traceback.format_exc())
            st.error(traceback.format_exc())
            continue

        if hasattr(report_instance, 'dataframe'):
            dataframe_sections[report_class.__name__] = i  # Store section position

    # Create navigation sidebar
    selected_section = st.sidebar.selectbox("Go to DataFrame:", list(dataframe_sections.keys()))
    # df_keys_string = ','.join(dataframe_sections.keys())
    with st.expander("Mito Spreadsheet Viewer"):
        dfs, code = spreadsheet(FullMetadataEnhanced(FRO).dataframe)
        st.code(code)

    # Display the selected DataFrame
    for report_class, section_index in dataframe_sections.items():
        if selected_section == report_class:
            report_instance = report_classes[section_index](FRO)  # Recreate instance

            st.write(f"DataFrame for {report_class}:")
            if hasattr(report_instance, "caption"):
                st.caption(report_instance.caption)
            st.dataframe(report_instance.dataframe)
            break  # Only display the selected section

def main(port=1967, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")

if __name__ == "__main__":
    run_streamlit_app()