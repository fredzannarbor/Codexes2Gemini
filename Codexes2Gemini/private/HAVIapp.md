# Codexes2LongContext (C2LC)

## Principal Investigator

- Fred Zimmerman, Publisher, Nimble Books LLC
- wfz@nimblebooks.com | NimbleBooks.com | 734-545-5369
- https://github.com/fredzannarbor/Codexes2Gemini

## Bio

Fred is a programmer, publisher, scientist, analyst and attorney with decades of experience at the intersection of technology and publishing, supporting diverse and sophisticated user communities such as NASA's Earth Observing System, the US intelligence community, and US and global public libraries, as well as publishing more than 300 books for readers of military, naval, and space history.

### tl;dr:

An opportunity to enable and shape the creation of a massively parallelized "latent space"  for potential books, in which millions of candidates are iteratively evolved towards highest possible quality and best fit with reader needs. The main vehicle for realizing this vision will be the creation of a Python library (C2LC) and using it to create a  demonstration "latent space" for books.

### Why Fund This Proposal

If the work in this domain of "latent space publishing" is left to big tech, big publishing, and academia--the default trajectory--the results will likely be both homogenized and scattered, a combination that is unlikely to provide maximum benefit to maximum readers. By driving open-source and user-driven exploration including the world of independent international publishing, Schmidt Sciences can dramatically accelerate the equitable delivery of a global benefit to human experience. The PI is a builder who combines a life-long academic-adjacent background with deep domain knowledge of book publishing and of important long-context objects such as science journals, legal cases, and specialized libraries.

### Scope

The C2LC library will include model-agnostic, localized, feature-extended, ground-truth-tested versions of the following modules, **all of which currently exist and work in prototype form.**. Some of these modules are available at http://github.com/fredzannarbor/Codexes2Gemini - `pip install Codexes2Gemini.`

- **Synthetic Reader:** a large language model and prompt generator that simulate the experience of human readers progressing page-by-page through a book, calibrated against real user behavior observed in the field and in device logs.
- **Audience Generator:** A set of personas who represent the target audience for a book. Instantiates a "core audience" theory based on the observation that most books (especially academic and scientific ones) sell fewer than 5,000 copies to small but coherent audiences.
- **Idea Forge:** generates many ideas & variations, feeds them to Synthetic Reader & Ideal Reader, iteratively evolves, evaluates, brings forward candiates for human evaluation.
- **Parts of the Book**: this module explicitly connects tokenized long-form objects with classes and methods for identifying and creating "parts of the book" such as introduction, tables, chapters, indexes, and appendices. 
- **Style**:  User prompts and system instructions guide the model to comply with specific rule sets, such as the Chicago Manual of Style, whose 18th edition (published 2024-08-22!) has been revised to reflect social change (inclusive language) as well as technical (emojis!)
- **Managing Editor**: calendaring, cost management, and so on.
- **Contributing Editor**: autonomous agents to maintain domain expertise and manage an imprint.
- **Editor-In-Chief**: portfolio management.
- **Cover Builder**: currently supports only a few trim sizes and styles. Extend.
- **Metadatas**: Large class with 130+ attributes that creates, optimizes, and manages all the information needed to submit a book to the two largest distributors, Ingram and Kindle Direct Publishing. 
- **Leo Bloom**: a financial analysis module that identifies patterns in publisher sales histories, Kindle sales ranks, and BookScan data and recommends actionable responses.

### Budget

| Role                                     |   | Comment              | FY2025  | FY2026  | FY2027  | FY2028  | FY2029  | Total     |
|------------------------------------------|---|----------------------|---------|---------|---------|---------|---------|-----------|
| PI fully loaded                   |   | 50% time             | 90,000  | 96,000  | 103,000 | 112,000 | 124,000 | 525,000   |
| User Research consulting                 |   |                      | 250,000 |         | 100,000 |         | 100,00  | 450,000   |
| Travel*                                  |   |                      | 40,000  | 42,000  | 44,000  | 47,000  | 52,000  | 225,000   |
| Equipment                                |   |                      | 10,000  | 1,000   | 1,000   | 10,000  | 1,000   | 23,000    |
| Developer (US midwest)        |   |                      | 250,000 | 270,000 | 295,000 | 325,000 | 355,000 | 1,500,000 |
| Assoc. Investigators x 2 (intl) |   | 50% time each, consultant |120,000  | 126,000  | 132,000  | 140,000  | 150,000  | 688,000   |
| GPU/API access costs(†)                  |   |                      | 150,000 | 250,000 | 300,000 | 150,000 | 150,000 | 1,000,000 |
| TOTALS                                   |   |                      | 760,000 | 785,000 | 975,000 | 874,000 | 932,000 | 4,326,000 |

† AI/ML requirements:

- Full realization of the project requires a "GPU rich" environment.
- The PI will work together with Schmidt Sciences to identify AI labs and researchers that are interested in contributing in kind. Frankly, **_Google Deepmind is the most logical partner,_** having done much of the pioneering research in long context windows and with access to the largest permissioned book corpus.
