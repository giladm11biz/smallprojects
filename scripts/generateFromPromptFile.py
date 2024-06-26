import requests
import base64
import os
import json
import time

PROMPT_FILE = "p.txt"
OUTPUT_DIR = "generated_images"
API_URL = "http://localhost:7860/sdapi/v1/txt2img"
NEGATIVE_PROMPT = "(nsfw, naked, nude, deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def read_prompts(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

def write_prompts(file_path, prompts):
    with open(file_path, 'w') as file:
        file.writelines(prompts)

def generate_images(prompt):
    payload = {
        "prompt": prompt.strip(),
        "negative_prompt": NEGATIVE_PROMPT,
        "alwayson_scripts": {
            "ADetailer": {
                "args": [
                    False, False, {
                        "ad_cfg_scale": 7,
                        "ad_checkpoint": "Use same checkpoint",
                        "ad_clip_skip": 1,
                        "ad_confidence": 0.3,
                        "ad_controlnet_guidance_end": 1,
                        "ad_controlnet_guidance_start": 0,
                        "ad_controlnet_model": "None",
                        "ad_controlnet_module": "None",
                        "ad_controlnet_weight": 1,
                        "ad_denoising_strength": 0.35,
                        "ad_dilate_erode": 4,
                        "ad_inpaint_height": 512,
                        "ad_inpaint_only_masked": True,
                        "ad_inpaint_only_masked_padding": 32,
                        "ad_inpaint_width": 512,
                        "ad_mask_blur": 4,
                        "ad_mask_k_largest": 0,
                        "ad_mask_max_ratio": 1,
                        "ad_mask_merge_invert": "None",
                        "ad_mask_min_ratio": 0,
                        "ad_model": "mediapipe_face_mesh_eyes_only",
                        "ad_model_classes": "",
                        "ad_negative_prompt": "",
                        "ad_noise_multiplier": 1,
                        "ad_prompt": "",
                        "ad_restore_face": False,
                        "ad_sampler": "DPM++ SDE Karras",
                        "ad_scheduler": "Use same scheduler",
                        "ad_steps": 28,
                        "ad_tab_enable": True,
                        "ad_use_cfg_scale": False,
                        "ad_use_checkpoint": False,
                        "ad_use_clip_skip": False,
                        "ad_use_inpaint_width_height": False,
                        "ad_use_noise_multiplier": False,
                        "ad_use_sampler": True,
                        "ad_use_steps": False,
                        "ad_use_vae": False,
                        "ad_vae": "Use same VAE",
                        "ad_x_offset": 0,
                        "ad_y_offset": 0,
                        "is_api": []
                    }
                ]
            }
        },
        "batch_size": 4,
        "cfg_scale": 1.5,
        "comments": {},
        "denoising_strength": 0.35,
        "disable_extra_networks": False,
        "do_not_save_grid": False,
        "do_not_save_samples": False,
        "enable_hr": True,
        "height": 768,
        "hr_negative_prompt": NEGATIVE_PROMPT,
        "hr_prompt": prompt.strip(),
        "hr_resize_x": 0,
        "hr_resize_y": 0,
        "hr_scale": 2,
        "hr_scheduler": "Automatic",
        "hr_second_pass_steps": 3,
        "hr_upscaler": "nmkdSiaxCX_200k",
        "n_iter": 1,
        "negative_prompt": NEGATIVE_PROMPT,
        "override_settings": {"use_downcasted_alpha_bar": True},
        "override_settings_restore_afterwards": True,
        "steps": 6,
        "tiling": False,
        "width": 512
    }

    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    return response.json()

def save_images(images):
    index = 1
    for image_data in images:
        image_path = os.path.join(OUTPUT_DIR, f"{int(time.time())}_{index}.png")
        with open(image_path, "wb") as img_file:
            img_file.write(base64.b64decode(image_data))
        index += 1

def main():
    prompts = read_prompts(PROMPT_FILE)
    total_prompts = len(prompts)
    
    while prompts:
        current_prompt = prompts[0]
        
        try:
            response = generate_images(current_prompt)
            if 'images' in response:
                save_images(response['images'])
                
                # Remove the successfully processed prompt
                prompts.pop(0)
                write_prompts(PROMPT_FILE, prompts)
                
                processed_prompts = total_prompts - len(prompts)
                print(f"Generated images for prompt: {current_prompt.strip()}")
                print(f"Saved images to: {OUTPUT_DIR}")
                print(f"Progress: {processed_prompts}/{total_prompts} done, {len(prompts)} remaining")
            else:
                print(f"Error in response for prompt: {current_prompt.strip()}")
                break
        except Exception as e:
            print(f"Error processing prompt: {current_prompt.strip()}")
            print(e)
            break

    # Check if the file is empty and delete it
    if not prompts:
        os.remove(PROMPT_FILE)
        print("All prompts processed and file deleted.")
    else:
        print("File is not empty, some prompts might have failed to process.")

if __name__ == "__main__":
    main()
