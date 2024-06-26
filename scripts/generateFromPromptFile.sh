#!/bin/bash

PROMPT_FILE="prompts.txt"
OUTPUT_DIR="generated_images"
API_URL="http://localhost:7860/api/v1/txt2img" # Replace with your actual API endpoint
TOTAL_PROMPTS=$(wc -l < "$PROMPT_FILE")

NEGATIVE_PROMPT="(nsfw, naked, nude, deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation"

mkdir -p "$OUTPUT_DIR"

while IFS= read -r PROMPT || [ -n "$PROMPT" ]; do
    # Remove the first line from the prompt file
    sed -i '1d' "$PROMPT_FILE"

    # Generate images using the API
    RESPONSE=$(curl -s -X POST "$API_URL" -H "Content-Type: application/json" -d '{
      "prompt": "'"$PROMPT"'",
      "negative_prompt": "'"$NEGATIVE_PROMPT"'",
      "alwayson_scripts": {
        "ADetailer": {
          "args": [
            false, false, {
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
              "ad_inpaint_only_masked": true,
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
              "ad_restore_face": false,
              "ad_sampler": "DPM++ SDE Karras",
              "ad_scheduler": "Use same scheduler",
              "ad_steps": 28,
              "ad_tab_enable": true,
              "ad_use_cfg_scale": false,
              "ad_use_checkpoint": false,
              "ad_use_clip_skip": false,
              "ad_use_inpaint_width_height": false,
              "ad_use_noise_multiplier": false,
              "ad_use_sampler": true,
              "ad_use_steps": false,
              "ad_use_vae": false,
              "ad_vae": "Use same VAE",
              "ad_x_offset": 0,
              "ad_y_offset": 0,
              "is_api": []
            }
          ]
        },
        "API payload": {"args": []},
        "Comments": {"args": []},
        "Composable Lora": {"args": [false, false, false]},
        "ControlNet": {
          "args": [
            {
              "advanced_weighting": null,
              "animatediff_batch": false,
              "batch_image_files": [],
              "batch_images": "",
              "batch_keyframe_idx": null,
              "batch_mask_dir": null,
              "batch_modifiers": [],
              "control_mode": "Balanced",
              "effective_region_mask": null,
              "enabled": false,
              "guidance_end": 1.0,
              "guidance_start": 0.0,
              "hr_option": "Both",
              "image": null,
              "inpaint_crop_input_image": false,
              "input_mode": "simple",
              "ipadapter_input": null,
              "is_ui": true,
              "loopback": false,
              "low_vram": false,
              "mask": null,
              "model": "None",
              "module": "none",
              "output_dir": "",
              "pixel_perfect": false,
              "processor_res": -1,
              "pulid_mode": "Fidelity",
              "resize_mode": "Crop and Resize",
              "save_detected_map": true,
              "threshold_a": -1.0,
              "threshold_b": -1.0,
              "weight": 1.0
            }
          ]
        },
        "Dynamic Thresholding (CFG Scale Fix)": {
          "args": [false, 7, 100, "Constant", 0, "Constant", 0, 4, true, "MEAN", "AD", 1]
        },
        "Extra options": {"args": []},
        "HakuBlend": {"args": []},
        "Hypertile": {"args": []},
        "ReActor": {
          "args": [
            null, false, "0", "0", "inswapper_128.onnx", "CodeFormer", 1, true,
            "None", 1, 1, false, true, 1, 0, 0, false, 0.5, true, false, "CUDA",
            false, 0, "None", "", null, false, false, 0.5, 0
          ]
        },
        "Refiner": {"args": [false, "", 0.8]},
        "Sampler": {"args": [6, "DPM++ SDE", "Automatic"]},
        "Seed": {"args": [-1, false, -1, 0, 0, 0]}
      },
      "batch_size": 4,
      "cfg_scale": 1.5,
      "comments": {},
      "denoising_strength": 0.35,
      "disable_extra_networks": false,
      "do_not_save_grid": false,
      "do_not_save_samples": false,
      "enable_hr": true,
      "height": 768,
      "hr_negative_prompt": "'"$NEGATIVE_PROMPT"'",
      "hr_prompt": "'"$PROMPT"'",
      "hr_resize_x": 0,
      "hr_resize_y": 0,
      "hr_scale": 2,
      "hr_scheduler": "Automatic",
      "hr_second_pass_steps": 3,
      "hr_upscaler": "nmkdSiaxCX_200k",
      "n_iter": 1,
      "override_settings": {"use_downcasted_alpha_bar": true},
      "override_settings_restore_afterwards": true,
      "steps": 6,
      "tiling": false,
      "width": 512
    }')

    # Extract image data from the response and save each image
    IMAGE_DATA_LIST=$(echo "$RESPONSE" | jq -r '.images[]')
    INDEX=1
    for IMAGE_DATA in $IMAGE_DATA_LIST; do
        IMAGE_PATH="$OUTPUT_DIR/$(date +%s)_$INDEX.png"
        echo "$IMAGE_DATA" | base64 --decode > "$IMAGE_PATH"
        INDEX=$((INDEX + 1))
    done

    # Show progress
    PROCESSED_PROMPTS=$(($TOTAL_PROMPTS - $(wc -l < "$PROMPT_FILE")))
    REMAINING_PROMPTS=$(wc -l < "$PROMPT_FILE")
    echo "Generated images for prompt: $PROMPT"
    echo "Saved images to: $OUTPUT_DIR"
    echo "Progress: $PROCESSED_PROMPTS/$TOTAL_PROMPTS done, $REMAINING_PROMPTS remaining"

done < "$PROMPT_FILE"

# Check if the file is empty and delete it
if [ ! -s "$PROMPT_FILE" ]; then
    rm "$PROMPT_FILE"
    echo "All prompts processed and file deleted."
else
    echo "File is not empty, some prompts might have failed to process."
fi
