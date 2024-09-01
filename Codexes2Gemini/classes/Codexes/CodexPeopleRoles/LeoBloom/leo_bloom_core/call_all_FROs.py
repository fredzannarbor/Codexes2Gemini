#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import os
import sys

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

import streamlit as st
import FinancialReportingObjects as FROs


def run_streamlit_app():
    report_classes = [
        FROs.LifetimePaidCompensation,
        FROs.EstimatedUnpaidCompensation,
        FROs.LSI_LTD_Paid_And_Unpaid_Compensation,
        FROs.ThisMonthUnitSales,
        FROs.FullMetadataIngest,
        FROs.FullMetadataEnhanced, FROs.Actual_Payment_History, FROs.AllUnitSalesThruToday  # SlowHorses
    ]

    FRO = FROs.FinancialReportingObjects()

    for report_class in report_classes:
        report_instance = report_class(FRO)

        st.write(f"DataFrame for {report_class.__name__}:")
        if hasattr(report_instance, 'dataframe'):
            df = report_instance.dataframe
            st.dataframe(df)
        else:
            st.write("This object can't be converted to a dataframe.")


def main(port=1967, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")


if __name__ == "__main__":
    run_streamlit_app()
