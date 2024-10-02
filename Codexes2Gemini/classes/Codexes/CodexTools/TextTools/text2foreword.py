import json

from app.utilities.gpt3complete import gpt3complete, chatcomplete


def create_preset_dict():
    foreword_presets = {'ForewordIntroWriter': "Foreword Introduction", 'ForewordMiddleWriter': "Foreword Middle",
                        'ForewordConclusionWriter': "Foreword Conclusion"}
    return foreword_presets


def create_foreword_in_one_step(title, author, description, output_dir):
    preset = 'ForewordOneStepWriter'
    prompt = f"\n\nInstructions: write the foreword to the book {title} by {author}. \n\nDescription: {description}. ]n\nUse personal anecdotes and vivid language.\n\n Explain why the topic is important, why the author is an expert, and why the reader must read this book. \n\nForeword: "
    response = gpt3complete(preset, prompt, engine="gpt-3.5-turbo")
    # print(response)
    response_text = chatcomplete(preset, prompt, engine="gpt-3.5-turbo")
    with open('output/responses.json', 'w') as f:
        json.dump(response_text, f)
    foreword = response_text

    return foreword


def create_publishers_note(title, author, description, output_dir, thisdoc_dir='currentdoc'):
    preset = 'PublishersNoteWriter'
    prompt = f"Title: {title}. \n\nAuthor: {author}. \n\nDescription:"
    response = gpt3complete(preset, prompt, engine="text-davinci-003")
    # print(response)

    publishersnote = response[0]['choices'][0]['text']
    with open(output_dir + thisdoc_dir + '/publishers_note.json', 'w') as f:
        json.dump(response, f)
    return publishersnote


if __name__ == "__main__":
    result = create_foreword_in_one_step("The Book of the Dead", "John Doe", "This is a book about the dead", "output/")
    print(result)
