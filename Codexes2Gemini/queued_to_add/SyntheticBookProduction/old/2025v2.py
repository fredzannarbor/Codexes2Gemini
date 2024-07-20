import json
import argparse
import logging
import uuid
import fitz
from classes.Utilities.utilities import configure_logger, set_logging_level

from classes.SyntheticBookProduction.Codexes2PartsOfTheBook import Codexes2Parts
from classes.SyntheticBookProduction.PromptPlan import PromptPlan

configure_logger("debug")

def pdf_to_text(pdf_file_path):
    return ''.join([page.get_text("text") for page in fitz.open(pdf_file_path).pages()])

def main():
    parser = argparse.ArgumentParser(description="Process PDF and generate chapters")
    parser.add_argument("--pdf_path", type=str, required=False, help="Path to the PDF file", default="/Users/fred/Downloads/2025_MandateForLeadership_FULL.pdf")
    parser.add_argument("--output_dir", type=str, required=False, help="Directory to save output files", default="output/editing")
    parser.add_argument("--prompts_file", "-p", type=str, required=False, help="Path to the JSON file containing prompts", default="resources/json/gemini_prompts/dark_baron_prompts.json")
    parser.add_argument("--system_message_file", type=str, required=False,
                        help="Path to the file containing the system message", default="resources/json/gemini_prompts/gemini_system_instructions.json")
    parser.add_argument("--persona", type=str, choices=["darkbaron", "squaddie"], required=False, help="Persona to use", default="darkbaron")
    parser.add_argument("--max_chapters", "-mc", type=int, default=3, help="Maximum number of chapters to process")
    parser.add_argument("--model_name", default="gpt-4o", help="Model to use")
    parser.add_argument("--desired_output_length", type=int, default=3800, help="Desired output length in characters")
    parser.add_argument("--no-context", "-nc", action='store_true', help="Do not use context")

    args = parser.parse_args()

    # Read system messages
    with open(args.system_message_file, 'r') as f:
        system_messages = json.load(f)

    try:
        system_message = system_messages[args.persona]
    except Exception as e:
        system_message = "You are an AI whose expertise is book publishing."
        logging.error(f"Error loading system message: {str(e)}")

    thisdoc_dir = args.output_dir + "/" + args.persona
    # Read prompts
    with open(args.prompts_file, 'r') as f:
        prompts = json.load(f)

    # Define list of keys based on persona
    listokeys = [f"chapter {i}" for i in range(1, 48)] if args.persona == "darkbaron" else [f"chapter {i}" for i in range(1, 31)] + ["conclusion"]

    if args.no_context:
        context = ""
        model_name = args.model_name
    else:
        context = pdf_to_text(args.pdf_path)
        model_name = "gemini-1.5-flash-001"

    # Initialize CodexesToBookParts
    c2b = Codexes2Parts()

    # Create PromptPlans
    plans = []
    for i, key in enumerate(listokeys[:args.max_chapters]):
        print(f"reading plan {i}")
        plan = PromptPlan(
            context=context,
            user_keys=[key],
            list_of_user_keys_to_use=key,
            thisdoc_dir=thisdoc_dir,
            model_name=model_name,
            json_required=False,
            generation_config={
                "temperature": 0.85,
                "top_p": 1.0,
                "max_output_tokens": args.desired_output_length
            },
            system_instructions_dict_file_path=args.system_message_file,
            list_of_system_keys=args.persona,
            user_prompt=prompts.get(key, ""),
            user_prompts_dict_file_path=args.prompts_file,
            continuation_prompts=False,
            output_file_path=f"{args.output_dir}/chapter_{i+1}.md",
            log_level="INFO",
            number_to_run=1,
            desired_output_length=args.desired_output_length
        )
        plans.append(plan)

    # Generate book parts
    book_parts = c2b.generate_full_book(plans)

    # Generate UUID for output files
    random_uuid = str(uuid.uuid4())[:6]

    # Save results
    with open(f"{thisdoc_dir}/results_{random_uuid}.json", 'w') as f:
        json.dump(book_parts, f)

    with open(f"{thisdoc_dir}/results_{random_uuid}.md", 'w') as f:
        f.write("\n\n".join(book_parts))

    print(f"Processing complete. Results saved in {thisdoc_dir}")

if __name__ == "__main__":
    set_logging_level("debug")
    main()