import os
import sys
import traceback

import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from Codexes2Gemini.classes.Codexes.Builders.PromptGroups import PromptGroups
from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher



class MultiContextProcessor:
    def __init__(self, context_groups, selected_prompt_group, selected_output_group):
        self.context_groups = context_groups
        self.selected_prompt_group = selected_prompt_group
        self.selected_output_group = selected_output_group

    def process_contexts(self):
        results = {}
        for group_name, file_paths in self.context_groups.items():  # Access file_paths directly
            group_results = []
            for file_path in file_paths:
                st.write(file_path)
                try:
                    with open(file_path, 'r') as file:
                        context = file.read()

                    # Process the context with the selected prompt group
                    result = self.process_single_context(context)
                    group_results.append(result)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    st.error(traceback.format_exc())
            results[group_name] = group_results
        return results

    def process_single_context(self, context):
        # Create a PromptBuilder instance
        prompt_builder = PromptGroups(
            self.selected_prompt_group.selected_system_instruction_keys,
            self.selected_prompt_group.selected_user_prompt_keys,
            self.selected_prompt_group.complete_user_prompt
        )

        # Build the prompt
        # prompt = prompt_builder.build_prompt(context)

        # Create a BuildLauncher instance
        launcher = BuildLauncher()

        # Prepare the arguments for BuildLauncher
        args = {
            'mode': self.selected_output_group.mode,
            'context': context,
            'output': self.selected_output_group.output_file,
            'selected_system_instructions': self.selected_prompt_group.selected_system_instruction_keys,
            'user_prompt': self.selected_prompt_group.complete_user_prompt,
            'selected_user_prompt_values': self.selected_prompt_group.selected_user_prompt_values,
            'list_of_user_keys_to_use': self.selected_prompt_group.selected_user_prompt_keys,
            'maximum_output_tokens': self.selected_output_group.maximum_output_tokens,
            'minimum_required_output': self.selected_output_group.minimum_required_output,
            'minimum_required_output_tokens': self.selected_output_group.minimum_required_output_tokens,
            'complete_user_prompt': self.selected_prompt_group.complete_user_prompt,
            'complete_system_instruction': self.selected_prompt_group.complete_system_instruction,
            'selected_system_instructions': self.selected_prompt_group.selected_system_instruction_keys,
            'selected_user_prompts_dict': self.selected_prompt_group.selected_user_prompts_dict,
        }

        # Run the BuildLauncher
        result = launcher.main(args)

        return result

    def save_results(self, results):

        for group_name, group_results in results.items():
            for i, result in enumerate(group_results):

                # Assuming you want to save each result as a separate file
                file_name = f"{group_name}_result_{i + 1}.txt"
                with open(file_name, 'w') as file:
                    try:
                        file.write(result[0][0])
                    except Exception as e:
                        st.error(traceback.format_exc())
                    st.info(f"Saved result to {file_name}")
                    st.write(result[0][0])
