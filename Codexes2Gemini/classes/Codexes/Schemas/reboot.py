from Codexes2Gemini.classes.Codexes.Builders.Codexes2PartsOfTheBook import Codexes2Parts
from Codexes2Gemini.classes.Codexes.Builders.PromptGroups import PromptGroups
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan


class Reboot:
    def __init__(self, context):
        self.context = context
        self.codexes2parts = Codexes2Parts()
        self.initial_prompts = [
            "gemini_get_basic_info",
            "create_reboot_prompts",
            "core_audience_attributes",
            "Create list of abbreviations",
            "create_ideal_reader_persona",
            "create_observables_for_reader"
        ]

    def run(self):
        # Step 1: Run initial prompts
        initial_plan = PromptsPlan(
            selected_user_prompt_keys=self.initial_prompts,
            context=self.context
        )
        initial_results = self.codexes2parts.process_codex_to_book_part(initial_plan)

        # Step 2: Extract reboot prompts
        reboot_prompts = self.extract_reboot_prompts(initial_results)
        print(reboot_prompts)

        # Step 3: Run reboot prompts
        reboot_plan = PromptsPlan(
            user_prompt_keys=reboot_prompts,
            context_text=self.context
        )

        reboot_results = self.codexes2parts.process_codex_to_book_part(reboot_plan)
        print(reboot_results[:250])

        # Step 4: Assemble into document
        document = self.assemble_document(reboot_results)
        print(document[0:250])
        return document

    def extract_reboot_prompts(self, initial_results):
        # TODO: Implement logic to extract "prompt" values from create_reboot_prompts response
        prompts = {}
        for k, v in initial_results:
            prompts.update({k: v})
        # make list of values
        return list(prompts.values())

    def assemble_document(self, reboot_results):
        # TODO: Implement logic to assemble results into a coherent document
        # For now, just return a concatenated string
        return "\n\n".join(reboot_results)


if __name__ == "__main__":
    context = "Your context text goes here"
    reboot_instance = Reboot(context)
    reboot_instance.run()
