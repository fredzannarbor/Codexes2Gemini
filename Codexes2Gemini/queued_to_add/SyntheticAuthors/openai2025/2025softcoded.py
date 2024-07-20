import json
import argparse
import logging
import traceback
import uuid
from openai import OpenAI
import fitz

def pdf_to_text(pdf_file_path):
    return ''.join([page.get_text("text") for page in fitz.open(pdf_file_path).pages()])


def simple_openai(client, system_message, user_message, model="gpt-4", temperature=0.85, max_tokens=3800):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            user_message,
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1.0)
    return response.choices[0].message.content


def process_chapters(client, system_message, prompts, listokeys, output_dir, max_chapters=100):
    results = []
    result_text = ''

    with open(f"{output_dir}/interim.txt", "w") as f:
        f.write("# DRAFT\n")

    print(system_message)


    for i, key in enumerate(listokeys):
        if i >= max_chapters:
            break
        user_message = {"role": "user", "content": f"{key}: {prompts.get(key)}"}
        print(user_message)
        if user_message["content"] is None:
            print(f"idx {i} is null")
            continue

        result = simple_openai(client, system_message, user_message)
        results.append(result)
        result_text += result

        with open(f"{output_dir}/interim.txt", 'a') as f:
            f.write(result_text)

        if i % 5 == 0:
            print(f'fetched result {i}')

    return results, result_text


def main():
    parser = argparse.ArgumentParser(description="Process PDF and generate chapters")
    parser.add_argument("--pdf_path", type=str, required=False, help="Path to the PDF file", default="/Users/fred/Downloads/2025_MandateForLeadership_FULL.pdf")
    parser.add_argument("--output_dir", type=str, required=False, help="Directory to save output files", default="output/editing")
    parser.add_argument("--prompts_file", type=str, required=False, help="Path to the JSON file containing prompts", default="resources/json/gemini_prompts/dark_baron_prompts.json")
    parser.add_argument("--system_message_file", type=str, required=False,
                        help="Path to the file containing the system message", default="resources/json/gemini_prompts/gemini_system_instructions.json")
    parser.add_argument("--persona", type=str, choices=["darkbaron", "squaddie"],required=False, help="Persona to use", default="darkbaron")
    parser.add_argument("--max_chapters", type=int, default=6, help="Maximum number of chapters to process")

    args = parser.parse_args()

    # Read system messages
    with open(args.system_message_file, 'r') as f:
        system_messages = json.load(f)

    try:
        system_message = system_messages[args.persona]
    except Exception as e:
        system_message = "You are an AI whose expertise is book publishing."
        logging.error(traceback.format_exc())



    # Read prompts
    with open(args.prompts_file, 'r') as f:
        prompts = json.load(f)

    if args.persona == "darkbaron":
        args.prompts_file = 'resources/json/gemini_prompts/dark_baron_prompts.json'
    elif args.persona == "squaddie":
        args.prompts_file == "resources/json/gemini_prompts/squaddie_prompts.json"

    # Define list of keys based on persona
    listokeys = [f"chapter {i}" for i in range(1, 48)] if args.persona == "darkbaron" else [f"chapter {i}" for i in
                                                                                            range(1, 31)] + [
                                                                                               "conclusion"]

    # Initialize OpenAI client
    client = OpenAI()

    # Process chapters
    results, result_text = process_chapters(client, system_message, prompts, listokeys, args.output_dir,
                                            args.max_chapters)

    # Generate UUID for output files
    random_uuid = str(uuid.uuid4())[:6]

    # Save results
    with open(f"{args.output_dir}/results_{random_uuid}.json", 'w') as f:
        json.dump(results, f)

    with open(f"{args.output_dir}/results_{random_uuid}.md", 'w') as f:
        f.write(result_text)

    print(f"Processing complete. Results saved in {args.output_dir}")


if __name__ == "__main__":
    main()