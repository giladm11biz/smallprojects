import requests
import os
import base64
import json
from PIL import Image
from io import BytesIO



# URL of the Fooocus API endpoint
api_url = "http://localhost:7866/v1/engine/generate/"

# Parameters for the API request
aspect_ratio = "1408*704"
performance = "Quality"
preset = "Realistic"
output_format = "png"
negative_prompt = "unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label, company logos, copyrighted logos, brand symbols, trademarks"
prompt = ""
base_model_name = "zavychromaxl_v80.safetensors"
image_dir = "for_upscale"
output_dir = "upscaled_images"

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

# Directory containing images to upscale
os.makedirs(output_dir, exist_ok=True)


def get_png_metadata(img):
    return 


def encode_image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
total_images = len(image_files)
current_image_num = 0

for image_file in image_files:
    current_image_num += 1
    image_path = os.path.join(image_dir, image_file)
    metadata = None
    image_base64 = None

    with Image.open(image_path) as img:
        metadata = img.info
        image_base64 = encode_image_to_base64(img)

    
    if (metadata and 'parameters' in metadata):
        original_image_parameters = json.loads(metadata['parameters'])
        prompt = original_image_parameters['full_prompt'][1]
        negative_prompt = original_image_parameters['negative_prompt'][1]

    print(f"Processing image {current_image_num}/{total_images}: {image_path}")

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
        "input_image_checkbox": True,
        "current_tab": "uov",
        "uov_method": "Upscale (2x)",
        "uov_input_image": image_base64,
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


    print(f"Upscaling 2x...")

    # Send the request to the API
    response = requests.post(api_url, json=payload)
    result = response.json()

    if response.status_code == 200:
        image_url = result['result'][0]
        image_base64 = base64.b64encode(requests.get(image_url).content).decode('utf-8')

        payload["uov_input_image"] = image_base64
        payload["uov_method"] = "Upscale (1.5x)"

        print(f"Upscaling 1.5x more...")
        response = requests.post(api_url, json=payload)
        # Get the result
        result = response.json()       

        # Handle the response
        if response.status_code == 200:
            image_url = result['result'][0]
            output_image_path = os.path.join(output_dir, f"upscaled_{image_file}")

            with Image.open(BytesIO(requests.get(image_url).content)) as img:
                # Create a copy of the image without the info dictionary
                img_no_metadata = Image.new(img.mode, img.size)
                img_no_metadata.putdata(list(img.getdata()))
                
                # Save the image without metadata
                img_no_metadata.save(output_image_path, "PNG")
                os.remove(image_path) # delete original image

            print(f"Successfully upscaled and saved")
        else:
            print(f"Failed to upscale 1.5 image: {image_path}")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    else:
        print(f"Failed to upscale 2x image: {image_path}")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
