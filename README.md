# Welcome to Codexes2Gemini

_Humans and AI making books richer, more diverse, and more surprising._

**Codexes** are books constructed of sheets of paper bound together.  

- Definitions and details are complex and multidimensional, but here's [a start (h/t Gemini)](https://g.co/gemini/share/57d3f2b1b163)
- [Well in excess of 150 million unique codexes](#References) have been created by humans.
- [Many, many billions](#References) of codex-length and codex-like documents exist in virtual formats such as docx and PDF.
- "...of making many books there is no end... " ([Ecclesiastes 12:12](https://www.biblegateway.com/passage/?search=Ecclesiastes%2012&version=KJV))
- 
**Gemini** is Latin for "twins", often referring to the half-brothers Castor and Pollux in Greek mythology.  Gemini is also the name of [Google's flagship generative AI model](https://gemini.google.com/), chosen to reflect the dual nature of language models, which are able to both understand and generate human language.  Gemini is a state-of-the-art large language model whose 2-million-token context window (July 2024) makes it ideally suitable for interacting with codexes.


This library provides tools for being creative with codexes!

## Installation

1. You can install the software via **pip install codexes2gemini.*  It's a good idea to create a virtual environment first, as C2G will install latest versions of various dependencies that may clash with your existing setup.
2. **You need to specify your Gemini API key as an environment variable.**  This is done by setting the `GEMINI_API_KEY` environment variable to your API key.  For example, on a Linux or macOS system, you could run the following command in your terminal:

   ```bash
   export GEMINI_API_KEY="your_api_key"

Replace "your_api_key" with your actual API key. You can find your API key in the Google Cloud Console.

3. There is an optional Streamlit front end to the C2G library. 

## Quick Starts

### Streamlit Front End
```bash
codexes2gemini-ui
```
The script will launch a tab in your default web browser.



## Key Features

- **Parts-of-the-Book Awareness**: Make your prompts and context fully aware of the inherent logical structure of codex books, known as the "parts of the book".
- **Facts and Assumptions In Context**:
- **Outline Generation:** Craft detailed outlines for codex books using your chosen personas.
- **Content Generation:**  Write entire books using a long codex as factual context for your outline.
- **Metadata Generation:**  Create rich metadata for your book based on its actual content, rather than assumptions.


## Demos

1. Create a pair of twinned author personas.
2. Write an outline for a codex book using those personas.
3. Use a very long codex book (920 pages) as factual context to that outline.
4. Write the book.
5. Create metadata for the book "bottom up" (based on what its content actually is) rather than "top down" (what authors and publishers _think_ it is.)

## References

“Books of the World, Stand up and Be Counted! All 129,864,880 of You.” n.d. Accessed July 23, 2024. http://booksearch.blogspot.com/2010/08/books-of-world-stand-up-and-be-counted.html.
“How Many Books Are In The World? (2024) - ISBNDB Blog.” 2023. October 20, 2023. https://isbndb.com/blog/how-many-books-are-in-the-world/.
Duff Johnson. 2018. “PDF Statistics – the Universe of Electronic Documents.” PDF Association. https://pdfa.org/wp-content/uploads/2018/06/1330_Johnson.pdf.

