import replicate


def text2midjourney_diffusion(prompt, negative_prompt='text', width=768, height=1024, prompt_strength=0.8,
                              num_outputs=1, num_inference_steps=50, guidance_scale=7.5, scheduler='DPMSolverMultistep',
                              seed=None):
    model = replicate.models.get("tstramer/midjourney-diffusion")
    version = model.versions.get("436b051ebd8f68d23e83d22de5e198e0995357afef113768c20f0b6fcef23c8b")
    mj_inputs = {
        'prompt': prompt,
        'negative_prompt': negative_prompt,
        'width': width,
        'height': height,
        'prompt_strength': prompt_strength,
        'num_outputs': num_outputs,
        'num_inference_steps': num_inference_steps,
        'guidance_scale': guidance_scale,
        'scheduler': scheduler,
        'seed': seed
    }
    mj_outputs = version.predict(mj_inputs)
    print(mj_outputs)

    return mj_outputs


if __name__ == "__main__":
    prompt = "Illustration for children's book called I HATE MY DADDY'S PHONE."
    negative_prompt = 'text'
    width = 768
    height = 1024
    prompt_strength = 0.8
    num_outputs = 1
    num_inference_steps = 50
    guidance_scale = 7.5
    scheduler = 'DPMSolverMultistep'
    seed = None
    testimages = text2midjourney_diffusion(prompt, negative_prompt, width, height, prompt_strength, num_outputs,
                                           num_inference_steps, guidance_scale, scheduler, seed)
