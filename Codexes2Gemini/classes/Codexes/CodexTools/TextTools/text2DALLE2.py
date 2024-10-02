import argparse
import os
import uuid

import openai
import requests

openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']


# helicone proxy


def create_DALLE2_images(prompt, n, dimensions, helicone_proxy):
    if helicone_proxy:
        openai.base_url = "https://oai.hconeai.com/v1"
    image_response = openai.Image.create(
        prompt=prompt,
        n=n,
        size=dimensions
    )
    print(f"Created {n} images with prompt: {prompt}")
    print(image_response)
    return image_response


def save_all_DALLE2_images(response, thisdoc_dir):
    if not os.path.exists(thisdoc_dir + '/DALLE2_images'):
        os.makedirs(thisdoc_dir + '/DALLE2_images')
    count = 0
    for item in response['data']:
        image_url = item['url']
        # uniq filename = six random letters from uuid
        filebase = str(uuid.uuid4())[:6]
        image_name = f"image_{filebase}.jpg"
        count += 1
        image_filepath = thisdoc_dir + '/DALLE2_images/' + image_name

        with open(image_filepath, "wb") as f:
            f.write(requests.get(image_url).content)
    print(f"Saved {count} images to {thisdoc_dir + '/DALLE2_images'}")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", "-p", type=str, default="AI for book-lovers", help="prompt for DALLE2 images")
    parser.add_argument("--number", "-n", type=int, default=1)
    parser.add_argument("--dimensions", "-d", type=str, default="512x512")
    parser.add_argument("--save_images", "-s", type=bool, default=False)
    parser.add_argument("--helicone_proxy", "-H", type=bool, default=True)
    args = parser.parse_args()
    prompt = args.prompt
    number = args.number
    dimensions = args.dimensions
    helicone_proxy = args.helicone_proxy
    save_images = args.save_images
    # explain why prompt can be undefined
    response = create_DALLE2_images(prompt, number, dimensions, helicone_proxy)
    if save_images:
        save_all_DALLE2_images(response)
