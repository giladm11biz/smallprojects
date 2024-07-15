import requests
import os

# URL of the Fooocus API endpoint
api_url = "http://localhost:7866/v1/engine/generate/"

# Parameters for the API request
aspect_ratio = "1408*704"
performance = "Quality"
preset = "Realistic"
image_number = 4
output_format = "png"
negative_prompt = "unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label, company logos, copyrighted logos, brand symbols, trademarks"
add_to_prompt = ", 8k, highly detailed, high quality" # Detailed natural skin and blemishes without-makeup and acne
base_model_name = "zavychromaxl_v80.safetensors"

# List of styles
styles = [
    "Fooocus V2",
    "Fooocus Enhance",
    "Fooocus Sharp",
    "Fooocus Photograph",
    "Fooocus Masterpiece",
    "Fooocus Negative",
    "Fooocus Cinematic"
]

# LoRA and model parameters
lora = [
    {"enabled": True, "model_name": "SDXL_FILM_PHOTOGRAPHY_STYLE_BetaV0.4.safetensors", "weight": 0.25},
    {"enabled": True, "model_name": "None", "weight": 1},
    {"enabled": True, "model_name": "None", "weight": 1},
    {"enabled": True, "model_name": "None", "weight": 1},
    {"enabled": True, "model_name": "None", "weight": 1}
]

# Directory to save generated images
output_dir = "generated_images"
os.makedirs(output_dir, exist_ok=True)

# File path for prompts
prompt_file = "p.txt"

# Read prompts from p.txt
with open(prompt_file, "r") as file:
    prompts = file.readlines()

total_prompts = len(prompts)
current_prompt_num = 0

def write_prompts(file_path, prompts):
    with open(file_path, 'w') as file:
        file.writelines(prompts)

while prompts:
    prompt = prompts.pop(0)
    prompt = prompt.strip() + add_to_prompt.strip()
    if not prompt:
        continue

    for run_num in range(image_number):
        current_prompt_num += 1
        print(f"Processing prompt {current_prompt_num}/{total_prompts * image_number}: {prompt} (Run {run_num + 1}/{image_number})")

        # Create the request payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "style_selections": styles,
            "performance_selection": performance,
            "aspect_ratios_selection": aspect_ratio,
            "image_number": 1,
            "output_format": output_format,
            "image_seed": -1,
            "read_wildcards_in_order": False,
            "sharpness": 2,
            "guidance_scale": 3,
            "base_model_name": base_model_name,
            "refiner_model_name": "None",
            "refiner_switch": 0.5,
            "loras": lora,
            "input_image_checkbox": False,
            "current_tab": "uov",
            "uov_method": "Disabled",
            "uov_input_image": "None",
            "outpaint_selections": [],
            "inpaint_input_image": "None",
            "inpaint_additional_prompt": "",
            "inpaint_mask_image_upload": "None",
            "disable_preview": False,
            "disable_intermediate_results": False,
            "disable_seed_increment": False,
            "black_out_nsfw": False,
            "adm_scaler_positive": 1.5,
            "adm_scaler_negative": 0.8,
            "adm_scaler_end": 0.3,
            "adaptive_cfg": 7,
            "clip_skip": 2,
            "sampler_name": "dpmpp_2m_sde_gpu",
            "scheduler_name": "karras",
            "vae_name": "Default (model)",
            "overwrite_step": -1,
            "overwrite_switch": -1,
            "overwrite_width": -1,
            "overwrite_height": -1,
            "overwrite_vary_strength": -1,
            "overwrite_upscale_strength": -1,
            "mixing_image_prompt_and_vary_upscale": False,
            "mixing_image_prompt_and_inpaint": False,
            "debugging_cn_preprocessor": False,
            "skipping_cn_preprocessor": False,
            "canny_low_threshold": 64,
            "canny_high_threshold": 128,
            "refiner_swap_method": "joint",
            "controlnet_softness": 0.25,
            "freeu_enabled": False,
            "freeu_b1": 1.01,
            "freeu_b2": 1.02,
            "freeu_s1": 0.99,
            "freeu_s2": 0.95,
            "debugging_inpaint_preprocessor": False,
            "inpaint_disable_initial_latent": False,
            "inpaint_engine": "v2.6",
            "inpaint_strength": 1,
            "inpaint_respective_field": 0.618,
            "inpaint_mask_upload_checkbox": False,
            "invert_mask_checkbox": False,
            "inpaint_erode_or_dilate": 0,
            "save_metadata_to_images": True,
            "metadata_scheme": "fooocus",
            "controlnet_image": [
                {
                    "cn_stop": 0.6,
                    "cn_type": "ImagePrompt",
                    "cn_weight": 0.5
                }
            ],
            "generate_image_grid": False,
            "outpaint_distance": [0, 0, 0, 0],
            "upscale_multiple": 1,
            "preset": "initial",
            "stream_output": False,
            "require_base64": False,
            "async_process": False,
            "webhook_url": ""
        }

        # Send the request to the API
        response = requests.post(api_url, json=payload)

        # Handle the response
        if response.status_code == 200:
            write_prompts(prompt_file, prompts)
            print(f"Success")
        else:
            print(f"Failed to generate images for prompt: {prompt}")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

# Delete the prompt file if it's empty
if os.stat(prompt_file).st_size == 0:
    os.remove(prompt_file)
    print(f"{prompt_file} is empty and has been deleted.")
