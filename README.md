# Welcome to Codexes2Gemini

_Humans and AIs making books richer, more diverse, and more surprising._

**Codexes** are books constructed of sheets of paper bound together.

- [Taxonomy](https://g.co/gemini/share/57d3f2b1b163) (h/t Gemini)

- [Well in excess of 150 million unique codexes](#References) have been created by humans.
- [Many, many billions](#References) of codex-length and codex-like documents exist in virtual formats such as docx and PDF.
- The codex's power to deliver immersive sharing of experience and deep knowledge makes it one of the most beneficial technologies ever created--[and we're just getting started!](https://nimblebooks.com/A_Longform_Prospectus#:~:text=The%20immersive%20deep%20reading%20of%20high%2Dquality%20books%20must%20rank%20among%20the%20most%20beneficial%20and%20broadly%20distributed%20technologies%20ever%20invented%20(see%20inter%20alia%20McLuhan%2C%201962%3B%20McDermott%2C%202006%3B%20Boorstin%2C%201992%3B%20UNESCO%202019).)
- "...of making many books there is no end... " ([Ecclesiastes 12:12](https://www.biblegateway.com/passage/?search=Ecclesiastes%2012&version=KJV))

A
selective, [annotated bibliography of AI research pertinent to book publishing.](https://NimbleBooks.com/Annotated_Bibliography)
Updated frequently.

**Gemini** is Latin for "twins", often referring to the half-brothers Castor and Pollux in Greek mythology. Gemini is
also the name of [Google's flagship generative AI model](https://gemini.google.com/), chosen to reflect the dual nature
of language models, which are able to both understand and generate human language. Gemini is a state-of-the-art large
language model whose 10-million-token context window for text (July 2024) makes it ideally suitable for interacting with
codexes.

Video I submitted to **Gemini API Developer Competition**:

https://github.com/user-attachments/assets/2da88d80-9173-4e57-b710-1711cda136ef



## Key Features

### Available Now

- **Metadata Generation:**  Create rich metadata for your book based on its actual content, rather than assumptions.
- **Parts-of-the-Book Awareness**: Make your prompts and context fully aware of the inherent logical structure of codex books, known as the "parts of the book".
- **Userspace with persistent, filterable contexts** from uploaded text, docx, and PDF documents.
- **Dictionaries of system and user prompts** that accomplish important publishing goals.

### Coming soon

- **Facts and Assumptions In Context**: Refer to the entire context of the corpus to ensure factuality in your
  generations.
- **Outline Generation:** Craft detailed outlines for codex books using your chosen personas.
- **Content Generation:**  Write entire books using a long codex as factual context for your outline.

## Installation

1. You can install the software via **pip install codexes2gemini.**  It's a good idea to create a virtual environment first, as C2G will install latest versions of various dependencies that may clash with your existing setup.
2. **You need to specify your Gemini API key as an environment variable.**  This is done by setting the `GEMINI_API_KEY` environment variable to your API key.  For example, on a Linux or macOS system, you could run the following command in your terminal:

   ```bash
   export GEMINI_API_KEY="your_api_key"

Replace "your_api_key" with your actual API key. You can find your API key in the Google Cloud Console. 

3. There is an optional Streamlit front end to the C2G library. 

4. To download the software so you can customize and enhance it:
```bash
git clone https://github.com/fredzannarbor/Codexes2Gemini.git
```
5. *Optional*: download the PG19 dataset of text files curated by Google Deepmind from Project Gutenberg. It is *large*: **11.74 GB**.  Place it in the data/ directory.

`cd Codexes2Gemini/data
git clone https://github.com/google-deepmind/pg19.git`

## Quick Starts

### Scripting

You can use the library to write your own Python scripts.

The file [quickstart.py](documentation/quickstart.py) contains simple illustrations of two ways you can
call the C2G classes in a Python script.

1.  Pass arguments in dictionary format to the appropriate Builder classes.

```from Codexes2Gemini.classes.Codexes.Builders import BuildLauncher

import json

launcher = BuildLauncher()


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

results = launcher.main(args1)
```

2. Create a JSON format PromptGroups object.

```import json

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
```

### Front Ends

The library comes with an optional Streamlit front end. It should be emphasized that this is strictly a demonstration,
the underlying function of the library does not depend on the choice of Streamlit. You could implement your own front
end using another UI package such as Flask or Django and if you do so your pull request will be appreciated!

#### Launch using Streamlit

It can be run from the second level of the repository like so:

`Codexes2Gemini> cd Codexes2Gemini
Codexes2Gemini/Codexes2Gemini> streamlit run ui/streamlit_ui.py --server.port=1455`

The server.port can be anything; 1455 is the year the Gutenberg Bible was published.

#### Launch via command script

The package also includes a command line script to launch the UI.

At the command line, type:

```bash
codexes2gemini-ui
```

The script will launch the streamlit web server as above. In other words, this is a useful shortcut.  It is the way I usually launch my production script.


## References

“Books of the World, Stand up and Be Counted! All 129,864,880 of You.” n.d. Accessed July 23, 2024. http://booksearch.blogspot.com/2010/08/books-of-world-stand-up-and-be-counted.html.

“How Many Books Are In The World? (2024) - ISBNDB Blog.” 2023. October 20, 2023. https://isbndb.com/blog/how-many-books-are-in-the-world/.

Duff Johnson. 2018. “PDF Statistics – the Universe of Electronic Documents.” PDF Association. https://pdfa.org/wp-content/uploads/2018/06/1330_Johnson.pdf.

