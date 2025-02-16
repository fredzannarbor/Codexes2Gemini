import os
import google.generativeai as genai

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# imagen = genai.ImageGenerationModel("imagen-3.0-generate-001")
# list available models
import pprint

for model in genai.list_models():
    pprint.pprint(model)
exit()
result = imagen.generate_images(
    prompt="Fuzzy bunnies in my kitchen",
    number_of_images=4,
    safety_filter_level="block_only_high",
    person_generation="allow_adult",
    aspect_ratio="3:4",
    negative_prompt="Outside",
)

for image in result.images:
    print(image)

for image in result.images:
    # Open and display the image using your local operating system.
    image._pil_image.show()
