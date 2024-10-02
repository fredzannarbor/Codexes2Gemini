import argparse

import replicate
import requests

model = replicate.models.get("tstramer/midjourney-diffusion")
version = model.versions.get("436b051ebd8f68d23e83d22de5e198e0995357afef113768c20f0b6fcef23c8b")


def run_replicate_model(inputs):
    output = version.predict(**inputs)
    print(output)
    result = requests.get(output[0])
    return result.url


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--prompt", "-P", type=str, default="AI for Book-Lovers")
    args.add_argument("--negative_prompt", type=str, default="text, photographs of people")
    args.add_argument("--width", type=int, default=768)
    args.add_argument("--height", type=int, default=1024)
    args.add_argument("--prompt_strength", type=float, default=0.8)
    args.add_argument("--num_outputs", type=int, default=1)
    args.add_argument("--num_inference_steps", type=int, default=50)
    args.add_argument("--guidance_scale", type=float, default=7.5)
    args.add_argument("--scheduler", type=str, default="DPMSolverMultistep")
    args.add_argument("--seed", type=int, default=None)
    args.add_argument("--outfilename", type=str, default="output/replicate-result.jpg")
    args.add_argument("--model", type=str, default="tstramer/midjourney-diffusion")
    args.add_argument("--version", type=str, default="436b051ebd8f68d23e83d22de5e198e0995357afef113768c20f0b6fcef23c8b")
    args.add_argument("--image_dimensions", type=str, default="768x768")

    args = args.parse_args()

    midjourney_inputs = {'prompt': args.prompt,
                         'negative_prompt': args.negative_prompt, -
                         'width': args.width,
                         'height': args.height,
                         'prompt_strength': args.prompt_strength,
                         'num_outputs': args.num_outputs,
                         'num_inference_steps': args.num_inference_steps,
                         'guidance_scale': args.guidance_scale,
                         'scheduler': args.scheduler,
                         'seed': args.seed,
                         'outfilename': args.outfilename,
                         'model': args.model,
                         'version': args.version}

    stable_diffusion_inputs = {'prompt': args.prompt,
                               'negative_prompt': args.negative_prompt,
                               'image_dimensions': args.image_dimensions,  # '768x768
                               'width': args.width,
                               'height': args.height,
                               'prompt_strength': args.prompt_strength,
                               'num_outputs': args.num_outputs,
                               'num_inference_steps': args.num_inference_steps,
                               'guidance_scale': args.guidance_scale,
                               'scheduler': args.scheduler,
                               'seed': args.seed,
                               'outfilename': args.outfilename,
                               'model': args.model,
                               'version': args.version}

    if args.model == "tstramer/midjourney-diffusion":
        inputs = midjourney_inputs
    elif args.model == "stability-ai/stable-diffusion":
        inputs = stable_diffusion_inputs
    image = run_replicate_model(inputs)
    # print(image)
    outfilename = inputs["outfilename"]
    with open(outfilename, 'wb') as f:
        get_response = requests.get(image)
        f.write(get_response.content)
    # webbrowser.open(outfilename)
