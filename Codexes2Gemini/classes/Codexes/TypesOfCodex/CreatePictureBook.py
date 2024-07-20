import os
from random import choice

import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def generate_unicorn_images(api_key, styles):
    openai.api_key = OPENAI_API_KEY

    for style in styles:
        situation = choice(["Harry Potter novel", "Star Trek novel", "Star Wars novel", "Lord of the Rings novel",
                            "Game of Thrones novel", "Dungeons and Dragons novel"])
        prompt = f"Create an image of a {style}. The image should be portrait orientation, 1024x768, and should be a highly realistic depiction of a unicorn in a setting from a  {situation} .\n\nImage:"
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            print(f"Generated {style} in {situation}: {image_url}")
        except Exception as e:
            print(f"Error generating {style}: {str(e)}")


# List of different unicorn styles
# unicorn_styles = [
#     "Crystal Unicorn", "Forest Guardian Unicorn", "Starlight Unicorn",
#     "Dimensional Rift Unicorn", "Elemental Fusion Unicorn"
unicorn_styles = ["Black Unicorn"]

generate_unicorn_images(OPENAI_API_KEY, unicorn_styles)
#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
