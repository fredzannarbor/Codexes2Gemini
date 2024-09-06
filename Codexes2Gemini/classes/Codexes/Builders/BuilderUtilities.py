import json

import pypandoc


def save_result_to_file_system(self, plan, result):
    unique_filename = f"{plan.thisdoc_dir}/{plan.output_file_path}_{str(uuid.uuid4())[:6]}"

    # convert markdown list to string
    md_result = "\n".join(result)
    with open(unique_filename + ".md", 'w') as f:
        f.write(md_result)
    with open(unique_filename + '.json', 'w') as f:
        json.dump(result, f, indent=4)
    self.logger.info(f"Output written to {unique_filename}.md and {unique_filename}.json")
    mainfont = 'Skolar PE'
    extra_args = ['--toc', '--toc-depth=2', '--pdf-engine=xelatex', '-V', f'mainfont={mainfont}',
                  '--pdf-engine=xelatex']
    try:
        pypandoc.convert_text(md_result, 'pdf', format='markdown', outputfile=unique_filename + ".pdf",
                              extra_args=extra_args)
        self.logger.info(f"PDF saved to {unique_filename}.pdf")
    except FileNotFoundError:
        self.logger.error("Pyandoc not found. Please install the pypandoc library to generate PDF.")


def truncate_dict_values(data, max_length=250):
    """
    Truncates string values in a dictionary to a specified maximum length.

    Args:
        data (dict): The dictionary to truncate.
        max_length (int): The maximum length for string values.

    Returns:
        dict: A new dictionary with truncated string values.
    """

    truncated_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            truncated_data[key] = value[:max_length]
        elif isinstance(value, dict):
            truncated_data[key] = truncate_dict_values(value, max_length)
        else:
            truncated_data[key] = value
    return truncated_data
