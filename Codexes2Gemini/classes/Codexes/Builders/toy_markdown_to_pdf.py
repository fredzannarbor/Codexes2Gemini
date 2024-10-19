from markdown_pdf import MarkdownPdf, Section

pdf = MarkdownPdf(toc_level=2)
pdf.add_section(Section("""# Condensed Matter

This book is a collection of essays and poetry about Garcilasso de la Vega. You'll learn about his life and poetry, as well as the history of Spanish poetry up until his time. 

The book is divided into a few parts:

* **Essay on Spanish Poetry:** This section explores the development of Spanish poetry,  highlighting the contributions of early poets like Juan de Mena and  Alfonso the Tenth, as well as those of the sixteenth century, including Garcilasso himself. 🤔
* **Life of Garcilasso:** You'll read about Garcilasso's  lineage, his early life, and his military career. ⚔️
* **Verses on the Death of Garcilasso:** Poems written about him in his honor by other poets. 💐
* **Garcilasso's Works:**  A translation into English verse of Garcilasso's poetry, including his eclogues, elegies, odes, and sonnets.  

**The author believes that Garcilasso is the most classical of all the Spanish poets and that his poems are deserving of admiration.**  🤩 He also offers a critical look at the history of Spanish poetry, highlighting the contributions of  other significant poets, as well as the shortcomings and extravagances of certain poets. 

You'll also see the author's  strong preference for Italian poetry as a model for English writers. He believes that the Italian style is still valuable today.  🇮🇹
""", paper_size="Card-4x6"))
pdf.save("49410test.pdf")
