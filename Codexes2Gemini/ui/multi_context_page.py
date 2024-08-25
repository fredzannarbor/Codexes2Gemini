# ui/multi_context_page.py
import os
import sys

import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
from Codexes2Gemini.classes.Codexes.Builders import PromptGroups
from Codexes2Gemini.classes.Codexes.Builders.MultiContextBuilder import MultiContextProcessor
from Codexes2Gemini.ui.utils import filter_dict, load_json_file
import os


class MultiContextUI:
    def __init__(self, user_space):
        self.user_space = user_space

    def render(self):
        st.header("Process Multiple Contexts")

        # Initialize multiplan in session state
        if 'multiplan' not in st.session_state:
            st.session_state.multiplan = []
        if 'current_plan' not in st.session_state:
            st.session_state.current_plan = {}

        context_groups = {}
        group_name = st.text_input("Enter a name for this group of contexts:")
        uploaded_files = st.file_uploader("Upload context files", accept_multiple_files=True)

        if uploaded_files:
            context_groups[group_name] = [file.name for file in uploaded_files]

        # --- Prompt Group Configuration (Reusing from multiplan_builder) ---

        user_prompts_dict = load_json_file("user_prompts_dict.json")
        system_instructions_dict = load_json_file("system_instructions.json")

        st.subheader("Step 2: Instructions and Prompts")

        # --- System Instructions ---
        with st.expander("Enter System Instructions"):
            system_filter = st.text_input("Filter system instructions")
            filtered_system = filter_dict(system_instructions_dict, system_filter)
            selected_system_instruction_values = []
            selected_system_instruction_keys = st.multiselect(
                "Select system instructions",
                options=list(filtered_system.keys()),
                format_func=lambda x: f"{x}: {filtered_system[x]['prompt'][:50]}..."
            )

            for key in selected_system_instruction_keys:
                selected_system_instruction_values.append(system_instructions_dict[key]['prompt'])

            complete_system_instruction = "\n".join(selected_system_instruction_values)

        # --- User Prompts ---
        with st.expander("Enter User Prompts"):
            user_filter = st.text_input("Filter user prompts")
            filtered_user = filter_dict(user_prompts_dict, user_filter)
            selected_user_prompt_keys = st.multiselect(
                "Select user prompt keys",
                options=list(filtered_user.keys()),
                format_func=lambda x: f"{x}: {filtered_user[x]['prompt'][:50]}..."
            )

            selected_user_prompt_values = [filtered_user[key]['prompt'] for key in selected_user_prompt_keys]
            selected_user_prompts_dict = {key: filtered_user[key]['prompt'] for key in selected_user_prompt_keys}

            custom_user_prompt = st.text_area("Custom User Prompt (optional)")
            user_prompt_override = st.radio("Override?",
                                            ["Override other user prompts", "Add at end of other user prompts"],
                                            index=1)
            if user_prompt_override == "Override other user prompts":
                complete_user_prompt = custom_user_prompt
            else:
                selected_user_prompt_keys.append("custom user prompt")
                complete_user_prompt = "\n".join(selected_user_prompt_values)

        # --- Form for Instructions and Prompts ---
        with st.form("multi_context_instructions_prompts"):
            if st.form_submit_button("Save Instructions and Prompts"):
                # Create a PromptGroup object (assuming your PromptGroups class constructor
                # takes the selected keys/values as arguments)
                selected_prompt_group = PromptGroups(
                    selected_system_instruction_keys=selected_system_instruction_keys,
                    selected_user_prompt_keys=selected_user_prompt_keys,
                    complete_user_prompt=complete_user_prompt
                )

        st.subheader("Step 3: Output Settings")
        with st.form("step3-output-settings"):
            with st.expander("Set Output Requirements"):
                mode_options = ["Single Part of a Book (Part)", "Full Codex (Codex)"]  # Add "Codex" option
                mode_mapping = {"Single Part of a Book (Part)": 'part',
                                "Full Codex (Codex)": 'codex'}  # Add mapping for "Codex"
                selected_mode_label = st.selectbox("Create This Type of Codex Object:", mode_options)
                mode = mode_mapping[selected_mode_label]
                if mode != 'codex':
                    maximum_output_tokens = st.number_input("Maximum output size in tokens", value=8000, step=500)
                    minimum_required_output = st.checkbox("Ensure Minimum Output", value=False)
                    minimum_required_output_tokens = st.number_input("Minimum required output tokens", value=50,
                                                                     step=500)
                else:
                    maximum_output_tokens = 10000000
                    minimum_required_output = False
                    minimum_required_output_tokens = 50

            with st.expander("Set Output Destinations"):
                thisdoc_dir = st.text_input("Output directory", value=os.path.join(os.getcwd(), 'output', 'c2g'))
                output_file = st.text_input("Output filename base", "output")
                log_level = st.selectbox("Log level", ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
                plan_name = st.text_input("Plan Name", value=st.session_state.current_plan.get('name', ''))

            if st.form_submit_button("Save Output Settings"):
                selected_output_group = PromptGroups(thisdoc_dir, output_file, log_level, mode, maximum_output_tokens,
                                                     minimum_required_output, minimum_required_output_tokens)

                st.session_state.multiplan.append(st.session_state.current_plan)
                st.success(f"Plan '{plan_name}' added to multiplan")
                st.session_state.current_plan = {}

        with st.form("process-contexts"):
            if st.form_submit_button("Process Contexts"):
                if not context_groups or not group_name:
                    st.warning("Please upload files and provide a group name.")
                elif not hasattr(selected_prompt_group, 'process'):  # Check if PromptGroup is configured
                    st.warning("Please configure and submit the Prompt Group settings.")
                else:
                    processor = MultiContextProcessor(context_groups, selected_prompt_group, selected_output_group)
                    results = processor.process_contexts()
                    processor.save_results(results)

                    st.subheader("Results:")
                    for group_name, group_results in results.items():
                        with st.expander(group_name):
                            for file_result in group_results:
                                st.markdown(file_result, unsafe_allow_html=True)
