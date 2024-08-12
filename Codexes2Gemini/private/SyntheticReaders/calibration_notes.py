#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

# with tab3:
#     with st.expander("Create New Reader Panels"):
#         # create new list of default reader attributes
#         attributes = Reader().attributes

# with tab2:
#     try:
#         #st.title("Calibrate Your Ratings")
#         st.write("On this page, you can rate the same ideas repeatedly, and see if the same idea gets the same score.")
#         with st.expander("More information"):
#             st.write("First, upload the ideas you want to rate.")
#             st.write("Then, rate the ideas yourself.")
#             st.write("Next, ask the system to rate your ideas repeatedly.")
#             st.write("See whether the system's ratings are consistent.")
#             st.write("Finally, compare the ratings you gave to the ratings the system gave.")
#     except Exception as e:
#         st.error(e)
#
#     with st.expander("Upload ideas"):
#         try:
#             uploaded_file = st.file_uploader("Upload ideas here.", key=(str(uuid4())[:6]))
#             if uploaded_file is not None:
#                 try:
#                     df = pd.read_csv(uploaded_file)
#                 except Exception as e:
#                     st.error(e)
#                 st.success("File uploaded successfully; you may make edits.")
#                 df = st.data_editor(df)
#             else:
#                 st.error("You must upload a csv file of ideas to proceed.")
#         except Exception as e:
#             st.error(e)
#
#     with st.expander("Choose Reader Panel"):
#         panel_df = cu.choose_reader_panel()
#         panel_df = st.data_editor(panel_df, num_rows="dynamic", key=(str(uuid4())[:6]))
#
#     with st.expander("Calibrate by multiple runs"):
#         if uploaded_file is not None:
#             with st.form("Calibrate by multiple runs"):
#                 run_result_df = pd.DataFrame()
#                 all_results_df = pd.DataFrame()
#                 number_of_runs = st.slider("How many times do you want to rate the same ideas?", 1, 10, 1)
#                 submitted = st.form_submit_button("Submit")
#                 if submitted:
#                     # submit_guard()
#                     for i in range(number_of_runs):
#                         st.info(f"Run {i + 1}")
#                         run_result_df = cu.rate_ideas(df, panel_df)
#                         all_results_df = pd.concat([all_results_df, run_result_df])
#                         # consistency = cu.evaluate_reader_consistency_per_idea(all_results_df)
#                     st.dataframe(all_results_df, hide_index=True)
#                     # st.write(f"Consistency: score {consistency}")
#         else:
#             st.error("You must upload a csv file of ideas to proceed.")

    # with st.expander("Rate Your Own ideas"):
    #     with st.form("Rate Your Own ideas")
    #         rated_ideas = st.data_editor(df)
    #         submitted = st.form_submit_button("Complete")
    #

