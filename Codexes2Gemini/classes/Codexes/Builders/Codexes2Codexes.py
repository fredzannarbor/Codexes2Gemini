import json

from classes.Codexes.Builders import Codexes2Parts, PromptGroups
from classes.Codexes.Builders.Codexes2PartsOfTheBook import parse_arguments


class Codex2Codex(Codexes2Parts):
    """
    Class for processing Codex to create another Codex.

    Attributes:
        logger (Logger): Logger instance for logging information.
        model_name (str): Name of the generative model to use.
        generation_config (dict): Configuration for generation process.
        safety_settings (list): List of safety settings for blocking harmful content.
        system_instructions_dict_file_path (str): Path to the system instructions dictionary file.
        continuation_instruction (str): Instruction for continuation prompts.
        results (list): List to store the generated book parts.
        add_system_prompt (str): Additional system prompt.

    Methods:
        configure_api(): Configures the API key.
        create_model(model_name, safety_settings, generation_config): Creates a generative model.
        process_codex_to_book_part(plan): Processes the Codex to generate a book part.
        count_tokens(text, model): Counts the number of tokens in a text.
        read_and_prepare_context(plan): Reads and prepares the context for generation.
        tokens_to_millions(tokens): Converts the number of tokens to millions.
        assemble_system_prompt(plan): Assembles the system prompt for generation.
        generate_full_book(plans): Generates the full book from a list of plans.
        gemini_get_response(plan, system_prompt, user_prompt, context, model): Calls the Gemini API to get the response.
        make_thisdoc_dir(plan): Creates the directory for the book part output.
    """

    def __init__(self):
        super().__init__()

    def process_codex_to_codex(self, plan: PromptGroups):
        return


args = parse_arguments()
c2b = Codexes2Parts()
plan = PromptGroups(
    context_file_paths=args.context_file_paths,
    user_keys=[args.list_of_user_keys_to_use.split(',')[0]],
    thisdoc_dir=args.thisdoc_dir,
    model_name=args.model,
    json_required=args.json_required,
    generation_config=json.loads(args.generation_config),
    system_instructions_dict_file_path=args.system_instructions_dict_file_path,
    list_of_system_keys=args.list_of_system_keys,
    user_prompt=args.user_prompt,
    user_prompt_override=args.user_prompt_override,
    user_prompts_dict_file_path=args.user_prompts_dict_file_path,
    list_of_user_keys_to_use=args.list_of_user_keys_to_use,
    continuation_prompts=args.continuation_prompts,
    output_file_base_name=args.output_file_path,
    log_level=args.log_level,
    number_to_run=args.number_to_run,
    minimum_required_output_tokens=args.minimum_required_output_tokens
)
book_part = c2b.process_codex_to_book_part(plan)
