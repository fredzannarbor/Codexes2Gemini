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

from Codexes2Gemini.classes.Codexes.Builders.BuildLauncher import BuildLauncher



class MultiContextProcessor:
    def __init__(self, context_groups, prompt_group):
        self.context_groups = context_groups
        self.prompt_group = prompt_group

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


        # Create a BuildLauncher instance
        launcher = BuildLauncher()

        # Prepare the arguments for BuildLauncher
        args = {
            'mode': self.prompt_group.mode,
            'context': context,
            'output': self.prompt_group.output_file,
            'selected_system_instructions': self.prompt_group.selected_system_instruction_keys,
            'user_prompt': self.prompt_group.complete_user_prompt,
            'selected_user_prompt_values': self.prompt_group.selected_user_prompt_values,
            'list_of_user_keys_to_use': self.prompt_group.selected_user_prompt_keys,
            'maximum_output_tokens': self.prompt_group.maximum_output_tokens,
            'minimum_required_output': self.prompt_group.minimum_required_output,
            'minimum_required_output_tokens': self.prompt_group.minimum_required_output_tokens,
            'complete_user_prompt': self.prompt_group.complete_user_prompt,
            'complete_system_instruction': self.prompt_group.complete_system_instruction,
            'selected_system_instructions': self.prompt_group.selected_system_instruction_keys,
            'selected_user_prompts_dict': self.prompt_group.selected_user_prompts_dict,
        }

        # Run the BuildLauncher
        result = launcher.main(args)

        return result

    def save_results(self, results):
        thisdoc_dir = self.prompt_group.thisdoc_dir
        output_file_name = self.prompt_group.output_file
        st.write(thisdoc_dir, output_file_name)
        st.write(results)

        for group_name, group_results in results.items():
            for i, result in enumerate(group_results):

                # Assuming you want to save each result as a separate file
                file_name = f"{thisdoc_dir}/{group_name}_{output_file_name}_{i + 1}.txt"
                with open(file_name, 'w') as file:
                    try:
                        file.write(result[0][0])
                    except Exception as e:
                        st.error(traceback.format_exc())
                    st.info(f"Saved result to {file_name}")
                    st.write(result[0][0])
