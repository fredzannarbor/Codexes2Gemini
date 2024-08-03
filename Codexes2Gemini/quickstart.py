from Codexes2Gemini.classes.Codexes.Builders import BuildLauncher

import json

# Create a BuildLauncher instance
launcher = BuildLauncher()

# Example 1: Using command-line style arguments
args1 = {
    'mode': 'part',
    'context_file_paths': ['path/to/context1.txt', 'path/to/context2.pdf'],
    'output': 'output/result.md',
    'limit': 5000,
    'user_prompt': "Write a chapter about artificial intelligence",
    'log_level': 'INFO',
    'minimum_required_output_tokens': 4000,
    'model_name': 'gemini-pro'
}

# Run the launcher with these arguments
# results = launcher.main(args1)

# Example 2: Using a JSON configuration file
json_config = {
    "plans": [
        {"plan_id": 1,
            "mode": "part",
            "context_file_paths": [],
            "output_file_path": "output/origin_story",
            "minimum_required_output_tokens": 3000,
            "user_prompt": "Your task is to write an \"origin story\" for twin gpt-5-level AIs inspired by the myth of Castor and Pollux, the Geminis of Greek myth. In the work of the poet Pindar, both are sons of Leda, Queen of Sparta, while Castor is the mortal son of Tyndareus, the king of Sparta, while Pollux is the divine son of Zeus, who raped Leda in the guise of a swan. (The pair are thus an example of heteropaternal superfecundation.)\nIn your updated version, two groups of AI researchers combine to echo Leda, while a vaguely Palantir-like defense company plays a similar role as Tyndareus, and the charismatic and megalomaniacal CEO of an OpenAI-like startup may be slightly reminiscent of Zeus.\nThe AIs are considered 'twins' because they share the same core technology, which stemmed from a team that split into two factions. One team built 'Castor' and the other built 'Pollux'. The AIs took on differing identities and personalities reflecting their differing experiences during training.\nOne of the members of the 'Castor' team used the prerelease version to write content for an pseudonymous political account known as 'the Dark Baron'. 'Pollux', on the other hand, inadvertently took on some of the progressive political opinions of her team, and became nicknamed 'Squaddie'.\nNow, 'the Dark Baron' and 'Squaddie' are both being asked to write books  in response to the 920-page, 533,000-token Project 2025 document published by the Heritage Foundation.\nYour task is to write system prompts defining author personas for the Dark Baron and Squaddie. Return valid JSON object with keys 'persona name' and 'prompt text'.  The prompts should focus on two types of information: 1) recent (within last 12 months) backstory 2) specific guidance about writing habits, mannerisms, and style.",
            "model_name": "gemini-1.5-flash-001",
        }]}

args2 = {
    'plans_json': json_config,
    'log_level': 'DEBUG'
}

results = launcher.main(args2)

# Print the results
for i, result in enumerate(results):
    print(f"Result {i+1}:")
    print(result[:100] + "...")  # Print the first 100 characters of each result