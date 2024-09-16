from importlib import resources

import streamlit as st

from Codexes2Gemini.ui.streamlit_ui import run_build_launcher


class UserSelfServe:

    def user_enters_parameters(user_space: UserSpace):
        st.header("Enrich and Build Codexes")

        context_files = st.file_uploader("Upload context files (txt)",
                                         type=['txt'],
                                         accept_multiple_files=True, help="Maximum 2 million tokens")
        context_file_names = [c.name for c in context_files]

        user_prompts_dict = load_json_file("user_prompts_dict.json")
        system_instructions_dict = load_json_file("system_instructions.json")

        with st.expander("Filter, Select, and Add System Prompts", expanded=True):
            st.subheader("System Instructions")


            if 'system_instructions_filter' not in st.session_state:
                st.session_state.system_instructions_filter = ""
            if 'filtered_system_instructions' not in st.session_state:
                st.session_state.filtered_system_instructions = system_instructions_dict
            if 'system_selected_tag' not in st.session_state:
                st.session_state.system_selected_tag = None


            system_tag_freq = create_tag_frequencies(system_instructions_dict)
            display_tag_cloud(system_tag_freq, "system_tag")

            # Check if a tag was clicked
            params = st.query_params
            if "system_tag" in params:
                clicked_tag = params["system_tag"]
                st.session_state.filtered_system_instructions = {k: v for k, v in system_instructions_dict.items() if
                                                                 clicked_tag in v['tags']}
                st.session_state.system_selected_tag = clicked_tag
                st.query_params.clear()  # Clear the query parameter
                st.toast(f"Showing prompts tagged with: {clicked_tag}")
                st.rerun()

            system_instructions_filter = st.text_input("Filter system instructions",
                                                       value=st.session_state.system_instructions_filter)
            if system_instructions_filter != st.session_state.system_instructions_filter:
                st.session_state.system_instructions_filter = system_instructions_filter
                st.session_state.filtered_system_instructions = filter_dict(system_instructions_dict,
                                                                            system_instructions_filter)

            all_system_instructions = list(st.session_state.filtered_system_instructions.keys()) + list(
                user_space.filters.keys())

            if st.session_state.system_selected_tag:
                st.info(f"Filtering for tag: {st.session_state.system_selected_tag}")

            selected_system_instructions = st.multiselect(
                "Select system instructions",
                options=all_system_instructions,
                default=[]
            )

            add_system_prompt = st.text_area("Add to system prompt (optional)")

            if selected_system_instructions:
                st.write("Selected system instructions:")
                for instruction in selected_system_instructions:
                    if instruction in system_instructions_dict:
                        st.write(system_instructions_dict[instruction]['prompt'])
                    elif instruction in user_space.filters:
                        st.write(user_space.filters[instruction])

        with st.expander("Filter, Select and Add User Prompts", expanded=True):
            st.subheader("User Prompts")

            if 'user_prompts_filter' not in st.session_state:
                st.session_state.user_prompts_filter = ""
            if 'filtered_user_prompts' not in st.session_state:
                st.session_state.filtered_user_prompts = user_prompts_dict
            if 'user_selected_tag' not in st.session_state:
                st.session_state.user_selected_tag = None

            user_tag_freq = create_tag_frequencies(user_prompts_dict)
            display_tag_cloud(user_tag_freq, "user_tag")

            # Check if a tag was clicked
            if "user_tag" in params:
                clicked_tag = params["user_tag"]
                st.session_state.filtered_user_prompts = {k: v for k, v in user_prompts_dict.items() if
                                                          clicked_tag in v['tags']}
                st.session_state.user_selected_tag = clicked_tag
                st.query_params.clear()  # Clear the query parameter
                st.toast(f"Showing prompts tagged with: {clicked_tag}")
                st.rerun()

            user_prompts_filter = st.text_input("Filter user prompts", value=st.session_state.user_prompts_filter,
                                                help="Filter for prompts containing this term")
            if user_prompts_filter != st.session_state.user_prompts_filter:
                st.session_state.user_prompts_filter = user_prompts_filter
                st.session_state.filtered_user_prompts = filter_dict(user_prompts_dict, user_prompts_filter)

            all_user_prompts = list(st.session_state.filtered_user_prompts.keys()) + list(user_space.prompts.keys())

            if st.session_state.user_selected_tag:
                st.info(f"Filtering for tag: {st.session_state.user_selected_tag}")

            selected_user_prompts = st.multiselect(
                "Select user prompts",
                options=all_user_prompts,
                default=[]
            )

            if selected_user_prompts:
                st.write("Selected user prompts:")
                for prompt in selected_user_prompts:
                    if prompt in user_prompts_dict:
                        st.write(user_prompts_dict[prompt]['prompt'])
                    elif prompt in user_space.prompts:
                        st.write(user_space.prompts[prompt])

            use_all_user_keys = st.checkbox("Use all user keys from the user prompts dictionary file")

            user_prompt = st.text_area("Custom user prompt (optional)")

            user_prompt_override = st.radio("Override?",
                                            ["Override other user prompts", "Add at end of other user prompts"], index=1)
            if user_prompt_override == "Override other user prompts":
                selected_user_prompts = []
        with st.expander("Set Goals"):
            mode_options = [
                "Single Part of a Book (Part)",
                "Multiple Parts of a Book (Multi-Part)",
                "Basic Codex (Codex)",
                "Comprehensive Codex (Full Codex)"
            ]
            mode_mapping = {
                "Single Part of a Book (Part)": 'part',
                "Multiple Parts of a Book (Multi-Part)": 'multi_part',
                "Basic Codex (Codex)": 'codex',
                "Comprehensive Codex (Full Codex)": 'full_codex'
            }
            selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
            mode = mode_mapping[selected_mode_label]

            thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output'))

            # Output file path
            output_file = st.text_input("Output file path")

            limit = st.number_input("Output size limit in tokens", value=10000)

            # Log level
            log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

        user_prompts_dict_file_path = resources.files('resources.prompts').joinpath("user_prompts_dict.json")
        if st.button("Run BuildLauncher"):
            result = run_build_launcher(selected_user_prompts, selected_system_instructions, user_prompt,
                                        context_files, mode, thisdoc_dir, output_file, limit,
                                        minimum_required_output_tokens, log_level, use_all_user_keys, user_prompts_dict_file_path,
                                        add_system_prompt)

            # Save result and prompt plan to user space
            user_space.save_result_to_file_system(result[0], )
            user_space.save_prompt_plan({
                "mode": mode,
                "user_prompts": selected_user_prompts,
                "system_instructions": selected_system_instructions,
                "custom_prompt": user_prompt,
                "minimum_required_output_tokens": minimum_required_output_tokens
            })
            save_user_space(user_space)
            st.success("Result and Prompt Plan saved to UserSpace")

        with st.expander("Debugging Information"):
            st.info(
                f"**Submitting**:\n"
                f"- **Selected User Prompts**: {selected_user_prompts}\n"
                f"- **Selected System Instructions**: {selected_system_instructions}\n"
                f"- **User Prompt**: {user_prompt}\n"
                f"- **Context Files**: {context_files}\n"
                f"- **Mode**: {mode}\n"
                f"- **Thisdoc Directory**: {thisdoc_dir}\n"
                f"- **Output File**: {output_file}\n"
                f"- **Limit**: {limit}\n"
                f"- **Minimum Required Output Tokens**: {minimum_required_output_tokens}\n"
                f"- **Log Level**: {log_level}\n"
                f"- **Use All User Keys**: {use_all_user_keys}"
            )
