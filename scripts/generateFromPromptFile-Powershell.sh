# Define variables
$PROMPT_FILE = "prompts.txt"
$OUTPUT_DIR = "generated_images"
$API_URL = "http://localhost:7860/api/v1/txt2img"
$NEGATIVE_PROMPT = "(nsfw, naked, nude, deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation"

# Create output directory if it doesn't exist
if (-not (Test-Path -Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR
}

# Read total prompts count
$TOTAL_PROMPTS = (Get-Content -Path $PROMPT_FILE).Count

while ($true) {
    # Read the first line (prompt) from the file
    $PROMPT = Get-Content -Path $PROMPT_FILE -First 1

    # Exit loop if no more prompts are available
    if (-not $PROMPT) {
        break
    }

    # Prepare the API payload
    $payload = @{
        prompt = $PROMPT
        negative_prompt = $NEGATIVE_PROMPT
        alwayson_scripts = @{
            ADetailer = @{
                args = @(
                    $false, $false, @{
                        ad_cfg_scale = 7
                        ad_checkpoint = "Use same checkpoint"
                        ad_clip_skip = 1
                        ad_confidence = 0.3
                        ad_controlnet_guidance_end = 1
                        ad_controlnet_guidance_start = 0
                        ad_controlnet_model = "None"
                        ad_controlnet_module = "None"
                        ad_controlnet_weight = 1
                        ad_denoising_strength = 0.35
                        ad_dilate_erode = 4
                        ad_inpaint_height = 512
                        ad_inpaint_only_masked = $true
                        ad_inpaint_only_masked_padding = 32
                        ad_inpaint_width = 512
                        ad_mask_blur = 4
                        ad_mask_k_largest = 0
                        ad_mask_max_ratio = 1
                        ad_mask_merge_invert = "None"
                        ad_mask_min_ratio = 0
                        ad_model = "mediapipe_face_mesh_eyes_only"
                        ad_model_classes = ""
                        ad_negative_prompt = ""
                        ad_noise_multiplier = 1
                        ad_prompt = ""
                        ad_restore_face = $false
                        ad_sampler = "DPM++ SDE Karras"
                        ad_scheduler = "Use same scheduler"
                        ad_steps = 28
                        ad_tab_enable = $true
                        ad_use_cfg_scale = $false
                        ad_use_checkpoint = $false
                        ad_use_clip_skip = $false
                        ad_use_inpaint_width_height = $false
                        ad_use_noise_multiplier = $false
                        ad_use_sampler = $true
                        ad_use_steps = $false
                        ad_use_vae = $false
                        ad_vae = "Use same VAE"
                        ad_x_offset = 0
                        ad_y_offset = 0
                        is_api = @()
                    }
                )
            }
        }
        batch_size = 4
        cfg_scale = 1.5
        comments = @{}
        denoising_strength = 0.35
        disable_extra_networks = $false
        do_not_save_grid = $false
        do_not_save_samples = $false
        enable_hr = $true
        height = 768
        hr_negative_prompt = $NEGATIVE_PROMPT
        hr_prompt = $PROMPT
        hr_resize_x = 0
        hr_resize_y = 0
        hr_scale = 2
        hr_scheduler = "Automatic"
        hr_second_pass_steps = 3
        hr_upscaler = "nmkdSiaxCX_200k"
        n_iter = 1
        negative_prompt = $NEGATIVE_PROMPT
        override_settings = @{
            use_downcasted_alpha_bar = $true
        }
        override_settings_restore_afterwards = $true
        steps = 6
        tiling = $false
        width = 512
    }

    # Convert the payload to JSON
    $payloadJson = $payload | ConvertTo-Json -Depth 10

    # Send the request to the API
    $response = Invoke-RestMethod -Uri $API_URL -Method Post -ContentType "application/json" -Body $payloadJson

    # Extract image data from the response and save each image
    $imageDataList = $response.images
    $index = 1
    foreach ($imageData in $imageDataList) {
        $imagePath = Join-Path -Path $OUTPUT_DIR -ChildPath "$(Get-Date -Format yyyyMMddHHmmss)_$index.png"
        [System.IO.File]::WriteAllBytes($imagePath, [System.Convert]::FromBase64String($imageData))
        $index++
    }

    # Remove the first line from the prompt file
    (Get-Content -Path $PROMPT_FILE) | Select-Object -Skip 1 | Set-Content -Path $PROMPT_FILE


    # Show progress
    $processedPrompts = $TOTAL_PROMPTS - (Get-Content -Path $PROMPT_FILE).Count
    $remainingPrompts = (Get-Content -Path $PROMPT_FILE).Count
    Write-Host "Generated images for prompt: $PROMPT"
    Write-Host "Saved images to: $OUTPUT_DIR"
    Write-Host "Progress: $processedPrompts/$TOTAL_PROMPTS done, $remainingPrompts remaining"
}

# Check if the file is empty and delete it
if (-not (Get-Content -Path $PROMPT_FILE)) {
    Remove-Item -Path $PROMPT_FILE
    Write-Host "All prompts processed and file deleted."
} else {
    Write-Host "File is not empty, some prompts might have failed to process."
}
