import csv
from typing import Dict

from .PromptGroups import PromptGroups


class CSV2PromptGroups(PromptGroups):
    """
    A class for creating CSV2PromptGroups objects from CSV data.

    Example Usage:
        plan = CSV2PromptGroups.from_csv_row(csv_row)
        plans = CSV2PromptGroups.from_csv_file(csv_file_path)

    """
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'CSV2PromptGroups':
        """Create a CSV2PromptGroups object from a CSV row."""
        # Convert CSV row data types to match PromptGroups's expected types
        data = {
            "context_file_paths": [row['context_file_path']],
            "user_keys": row['user_keys'].split(',') if row['user_keys'] else [],
            "thisdoc_dir": row['thisdoc_dir'],
            "json_required": row['json_required'].lower() == 'true',
            "generation_config": {
                "temperature": float(row['temperature']),
                "top_p": float(row['top_p']),
                "top_k": int(row['top_k']),
                "max_output_tokens": int(row['max_output_tokens'])
            },
            "system_instructions_dict_file_path": row['system_instructions_dict_file_path'],
            "list_of_system_keys": row['list_of_system_keys'],
            "user_prompt": row['user_prompt'],
            "user_prompt_override": row['user_prompt_override'].lower() == 'true',
            "user_prompts_dict_file_path": row['user_prompts_dict_file_path'],
            "list_of_user_keys_to_use": row['list_of_user_keys_to_use'],
            "continuation_prompts": row['continuation_prompts'].lower() == 'true',
            "output_file_base_name": row['output_file_base_name'],
            "log_level": row['log_level'],
            "number_to_run": int(row['number_to_run']),
            "minimum_required_output_tokens": int(row['minimum_required_output_tokens']),
            "model_name": row['model_name'],
            "use_all_user_keys": row['use_all_user_keys'].lower() == 'true'
        }
        return cls(**data)

    @classmethod
    def from_csv_file(cls, csv_file_path: str) -> Dict[str, List['CSV2PromptGroups']]:
        """Create CSV2PromptGroups objects from a CSV file."""
        plans = {}
        with open(csv_file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                file_name = row['output_file_name']
                plan = cls.from_csv_row(row)
                if file_name not in plans:
                    plans[file_name] = []
                plans[file_name].append(plan)
        return plans


def create_prompt_plan_files(csv_file_path: str, output_dir: str):
    """Create PromptGroups JSON files from a CSV file."""
    plans = CSV2PromptGroups.from_csv_file(csv_file_path)

    for file_name, prompt_plans in plans.items():
        output_path = os.path.join(output_dir, file_name)
        with open(output_path, 'w') as json_file:
            json.dump({"plans": [plan.to_dict() for plan in prompt_plans]}, json_file, indent=2)

    print(f"Created {len(plans)} PromptGroups JSON file(s) in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Create PromptGroups JSON files from a CSV file.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input CSV file")
    parser.add_argument('-o', '--output', required=True, help="Path to the output directory for JSON files")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} does not exist.")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Created output directory: {args.output}")

    create_prompt_plan_files(args.input, args.output)


if __name__ == "__main__":
    main()