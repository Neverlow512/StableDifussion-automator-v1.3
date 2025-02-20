#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
import base64
import argparse
import logging
from tqdm import tqdm  # For progress bar

# For keyboard listener
try:
    import pynput
    from pynput import keyboard
except ImportError:
    print("The 'pynput' module is required for pause functionality. Installing it now...")
    os.system(f"{sys.executable} -m pip install pynput")
    import pynput
    from pynput import keyboard

paused = False  # Global variable to control pause state
keyboard_listener = None  # Global variable for keyboard listener

def on_press(key):
    global paused
    try:
        if key == keyboard.Key.f8:
            paused = not paused
            state = "Paused" if paused else "Resumed"
            print(f"\n{state}...")
    except AttributeError:
        pass

def start_keyboard_listener():
    global keyboard_listener
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

def stop_keyboard_listener():
    global keyboard_listener
    if keyboard_listener is not None:
        keyboard_listener.stop()
        keyboard_listener = None

def load_sd_settings():
    settings_dir = os.path.join(os.getcwd(), 'settings')
    sd_settings_path = os.path.join(settings_dir, 'sd_settings.json')
    if not os.path.exists(sd_settings_path):
        print("Error: sd_settings.json not found. Please create it in the 'settings' directory.")
        sys.exit(1)
    with open(sd_settings_path, 'r') as f:
        return json.load(f)

def load_prompts(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return [block.strip() for block in content.split('---') if block.strip()]

def parse_prompt_block(block):
    lines = block.strip().split('\n')
    data = {}
    current_key = None
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            current_key = key.strip()
            data[current_key] = value.strip()
        else:
            if current_key:
                data[current_key] += ' ' + line.strip()
    # Handle the 'LoRAs' key if present
    if 'LoRAs' in data:
        loras = data['LoRAs']
        # Split the LoRAs by commas and strip whitespace
        data['LoRAs'] = [lora.strip() for lora in loras.split(',') if lora.strip()]
    else:
        data['LoRAs'] = []
    # Handle the 'Characters' key if present (for scenes)
    if 'Characters' in data:
        characters = data['Characters']
        # Split the characters by commas and strip whitespace
        data['Characters'] = [char.strip() for char in characters.split(',') if char.strip()]
    else:
        data['Characters'] = []
    return data

def create_prompts(prompt_type, folder_path):
    if prompt_type == 'character':
        prompts_file = os.path.join(folder_path, 'characters.txt')
    else:
        prompts_file = os.path.join(folder_path, 'scenes.txt')

    prompt_blocks = load_prompts(prompts_file)
    prompts = []
    for block in prompt_blocks:
        data = parse_prompt_block(block)
        prompts.append(data)
    return prompts

def get_available_models(sd_models_path):
    model_extensions = ('.ckpt', '.safetensors', '.pt')
    models = [f for f in os.listdir(sd_models_path) if os.path.isfile(os.path.join(sd_models_path, f)) and f.lower().endswith(model_extensions)]
    return models

def get_available_loras(lora_dir):
    """Retrieve a list of available LoRA models from the specified directory."""
    lora_extensions = ('.safetensors', '.ckpt', '.pt')  # Add other extensions if needed
    if not os.path.exists(lora_dir):
        print(f"LoRA directory '{lora_dir}' does not exist.")
        return []
    loras = [f for f in os.listdir(lora_dir) if os.path.isfile(os.path.join(lora_dir, f)) and f.lower().endswith(lora_extensions)]
    return loras

def select_loras(loras):
    """Prompt the user to select one or more LoRAs from the available list and specify their weights."""
    if not loras:
        print("No LoRA models found.")
        return []
    
    print("\nAvailable LoRA Models:")
    for idx, lora in enumerate(loras, start=1):
        print(f"{idx}: {lora}")
    print("0: No LoRA")
    
    selected_loras = []
    while True:
        choice = input("Select LoRAs by entering numbers separated by commas (e.g., 1,3) or '0' for no LoRA: ").strip()
        if choice == '0':
            return []
        selected_indices = [x.strip() for x in choice.split(',')]
        try:
            selected_loras = [loras[int(idx)-1] for idx in selected_indices if idx.isdigit() and 1 <= int(idx) <= len(loras)]
            if selected_loras:
                break
            else:
                print("No valid LoRA selections made. Please try again.")
        except (IndexError, ValueError):
            print("Invalid input. Please enter valid numbers separated by commas.")
    
    # Prompt for weights
    loras_with_weights = []
    print("\nAssign weights to the selected LoRAs (default is 0.75).")
    for lora in selected_loras:
        while True:
            weight_input = input(f"Enter weight for '{lora}' (0.0 to 1.0, default 0.75): ").strip()
            if weight_input == '':
                weight = 0.75
                break
            try:
                weight = float(weight_input)
                if 0.0 <= weight <= 1.0:
                    break
                else:
                    print("Weight must be between 0.0 and 1.0. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a numeric value between 0.0 and 1.0.")
        loras_with_weights.append({"name": os.path.splitext(lora)[0], "weight": weight})
    
    return loras_with_weights

def get_available_samplers(api_endpoint):
    try:
        response = requests.get(f'{api_endpoint}/sdapi/v1/samplers')
        response.raise_for_status()
        samplers = response.json()
        return [sampler['name'] for sampler in samplers]
    except Exception as e:
        print(f"Error fetching samplers: {e}")
        return []

def get_available_schedulers(api_endpoint):
    try:
        response = requests.get(f'{api_endpoint}/sdapi/v1/schedulers')
        response.raise_for_status()
        schedulers = response.json()
        return [scheduler['name'] for scheduler in schedulers]
    except Exception as e:
        print(f"Error fetching schedulers: {e}")
        return []

def check_stable_diffusion_running(api_endpoint):
    # Check if the web UI is already running
    test_url = f'{api_endpoint}/sdapi/v1/sd-models'
    print(f"Checking if Stable Diffusion web UI is running at {test_url}...")
    try:
        response = requests.get(test_url)
        if response.status_code == 200:
            print("Stable Diffusion web UI is running.")
            return True
        else:
            print(f"Received unexpected status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def generate_json_files(prompts, prompt_type, story_name, default_seed, num_images, num_iterations, output_dir):
    base_dir = os.path.join(output_dir, story_name, 'Characters' if prompt_type == 'character' else 'Scenes')
    os.makedirs(base_dir, exist_ok=True)
    json_files = []
    for data in prompts:
        item_name = data.get('Name', 'Unnamed').replace(' ', '_')
        item_dir = os.path.join(base_dir, item_name)
        os.makedirs(item_dir, exist_ok=True)
        prompt_path = os.path.join(item_dir, 'prompt.json')
        # Remove 'Name' from data to avoid redundancy in JSON
        data_without_name = {k: v for k, v in data.items() if k != 'Name'}
        # Set global 'Number of Images', 'Number of Iterations', and 'Seed'
        data_without_name['Number of Images'] = num_images
        data_without_name['Number of Iterations'] = num_iterations
        data_without_name['Seed'] = default_seed
        with open(prompt_path, 'w', encoding='utf-8') as f:
            json.dump(data_without_name, f, indent=4)
        json_files.append(prompt_path)
    return json_files

def generate_images(settings, prompt_type, story_name, num_images, num_iterations, output_dir, character_prompts, selected_loras, lora_dir):
    api_url = settings.get('api_endpoint', 'http://localhost:7860') + '/sdapi/v1/txt2img'
    headers = {'Content-Type': 'application/json'}

    base_dir = os.path.join(output_dir, story_name, 'Characters' if prompt_type == 'character' else 'Scenes')
    if not os.path.exists(base_dir):
        print(f"No {prompt_type}s to process in {story_name}.")
        return
    items = os.listdir(base_dir)
    for item_name in items:
        item_dir = os.path.join(base_dir, item_name)
        prompt_path = os.path.join(item_dir, 'prompt.json')
        if not os.path.exists(prompt_path):
            continue
        with open(prompt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        seed = int(data.get('Seed', settings['seed']))
        if seed == -1:
            seed = int(time.time())  # Use current time as seed if -1

        print(f"\nGenerating images for {prompt_type}: {item_name}")
        print(f"Settings:")
        print(f"  Model: {settings['model']}")
        if selected_loras:
            lora_names = ', '.join([f"{lora['name']} ({lora['weight']})" for lora in selected_loras])
            print(f"  LoRAs: {lora_names}")
        else:
            print(f"  LoRAs: None")
        print(f"  Sampler: {settings['sampling_method']}")
        print(f"  Scheduler: {settings['scheduler']}")
        print(f"  Sampling Steps: {settings['sampling_steps']}")
        print(f"  Width: {settings['width']}")
        print(f"  Height: {settings['height']}")
        print(f"  CFG Scale: {settings['cfg_scale']}")
        print(f"  Seed: {seed}")
        print(f"  Number of Images: {num_images}")
        print(f"  Number of Iterations: {num_iterations}")

        for iteration in range(1, num_iterations + 1):
            iteration_dir = os.path.join(item_dir, f'Iteration_{iteration}')
            os.makedirs(iteration_dir, exist_ok=True)

            positive_prompt = data.get('Positive prompt', '')
            negative_prompt = data.get('Negative prompt', '')

            # Include character details in the prompt
            if prompt_type == 'character':
                # For character images, use the character's own description
                character_description = data.get('Description', '')
                positive_prompt += f" {character_description}"
            elif prompt_type == 'scene':
                # For scenes, include descriptions of characters present
                scene_characters = data.get('Characters', [])
                for character_name in scene_characters:
                    # Find the character's description
                    character = next((c for c in character_prompts if c['Name'] == character_name), None)
                    if character:
                        character_description = character.get('Description', '')
                        positive_prompt += f" {character_description}"

            # Append LoRA references with weights to the positive prompt
            if selected_loras:
                # Format: " <lora:LoRA_Name:Weight> <lora:LoRA_Name:Weight> ..."
                lora_references = " ".join([f"<lora:{lora['name']}:{lora['weight']}>" for lora in selected_loras])
                positive_prompt += f" {lora_references}"

            # Use unique identifier or token if available
            unique_identifier = data.get('Unique Identifier', '')
            if unique_identifier:
                positive_prompt += f" {unique_identifier}"

            # Check for pause
            while paused:
                time.sleep(0.5)

            payload = {
                "prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "steps": settings["sampling_steps"],
                "cfg_scale": settings["cfg_scale"],
                "width": settings["width"],
                "height": settings["height"],
                "sampler_name": settings["sampling_method"],
                "seed": seed,
                "batch_size": 1,
                "n_iter": num_images,
                "scheduler": settings["scheduler"],
                "override_settings": {
                    "sd_model_checkpoint": settings["model"]
                }
            }

            # Log the payload
            logging.info(f"Generating images for {item_name}, Iteration {iteration}")
            logging.info(f"Payload: {json.dumps(payload, indent=4)}")

            print(f"\nIteration {iteration}: Generating {num_images} images...")
            try:
                response = requests.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                r = response.json()

                # Log the response
                logging.info(f"Response: {response.text}")

                for idx, img_data in enumerate(tqdm(r['images'], desc=f"Saving images for {item_name}")):
                    img_bytes = base64.b64decode(img_data)
                    img_path = os.path.join(iteration_dir, f'{item_name}_{iteration}_{idx + 1}.png')
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_bytes)
                print(f"Iteration {iteration}: Completed generating images for {item_name}")
            except requests.exceptions.RequestException as e:
                print(f"Error generating images for {item_name} in iteration {iteration}: {e}")
                logging.error(f"Error generating images for {item_name} in iteration {iteration}: {e}")
                continue

            # Check for pause
            while paused:
                time.sleep(0.5)

def main():
    # Configure logging
    logging.basicConfig(filename='generation_log.txt', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

    # Load Stable Diffusion settings
    sd_settings = load_sd_settings()

    # Check if Stable Diffusion web UI is running
    api_endpoint = sd_settings.get("api_endpoint", "http://localhost:7860")
    if not check_stable_diffusion_running(api_endpoint):
        print("Stable Diffusion web UI is not running.")
        print("Please start the web UI manually before running this script.")
        sys.exit(1)

    # Use the input directory in the same directory as the script
    script_dir = os.getcwd()
    input_dir = os.path.join(script_dir, 'input')
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    # Create the output directory if it doesn't exist
    output_dir = os.path.join(script_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Define the LoRA directory based on Automatic1111's structure
    lora_dir = os.path.join(sd_settings['sd_folder'], 'models', 'Lora')

    # Detect available LoRAs
    available_loras = get_available_loras(lora_dir)

    # Prompt user to select LoRAs
    selected_loras = select_loras(available_loras)

    # Get list of folders in the input directory
    available_folders = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    if not available_folders:
        print(f"No folders found in '{input_dir}'.")
        sys.exit(1)

    # Display available folders
    print("\nAvailable Folders:")
    for idx, folder_name in enumerate(available_folders, start=1):
        print(f"{idx}: {folder_name}")
    print("0: All folders")

    # Prompt user to select folders
    folder_choices = input("Select folders to process by entering numbers separated by commas (e.g., 1,3,5) or '0' for all: ").strip()
    if folder_choices == '0':
        selected_folders = available_folders
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in folder_choices.split(',') if x.strip().isdigit()]
            selected_folders = [available_folders[idx] for idx in selected_indices if 0 <= idx < len(available_folders)]
        except ValueError:
            print("Invalid input. Exiting.")
            sys.exit(1)

    if not selected_folders:
        print("No valid folders selected.")
        sys.exit(1)

    # Get global settings from user input
    # Get available models
    sd_folder = sd_settings['sd_folder']
    models_path = os.path.join(sd_folder, 'models', 'Stable-diffusion')

    models = get_available_models(models_path)
    if not models:
        print(f"No models found in '{models_path}'.")
        sys.exit(1)

    # Select model
    print("\nAvailable Models:")
    for idx, model in enumerate(models):
        print(f"{idx + 1}: {model}")
    while True:
        try:
            model_choice = int(input("Select a model by number: ")) - 1
            if 0 <= model_choice < len(models):
                model = models[model_choice]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Select schedulers
    schedulers = get_available_schedulers(api_endpoint)
    if not schedulers:
        print("No schedulers available. Exiting.")
        sys.exit(1)

    # Select scheduler
    print("\nAvailable Schedulers:")
    for idx, scheduler in enumerate(schedulers):
        print(f"{idx + 1}: {scheduler}")
    while True:
        try:
            scheduler_choice = int(input("Select a scheduler by number: ")) - 1
            if 0 <= scheduler_choice < len(schedulers):
                scheduler = schedulers[scheduler_choice]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Select samplers
    samplers = get_available_samplers(api_endpoint)
    if not samplers:
        print("No samplers available. Exiting.")
        sys.exit(1)

    # Select sampler
    print("\nAvailable Samplers:")
    for idx, sampler in enumerate(samplers):
        print(f"{idx + 1}: {sampler}")
    while True:
        try:
            sampler_choice = int(input("Select a sampler by number: ")) - 1
            if 0 <= sampler_choice < len(samplers):
                sampling_method = samplers[sampler_choice]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    # Prompt user to select LoRAs and assign weights
    print("\n--- LoRA Selection ---")
    selected_loras = select_loras(available_loras)

    # Ask for other settings
    while True:
        try:
            sampling_steps = int(input("Enter the number of sampling steps (default 50): ").strip() or 50)
            break
        except ValueError:
            print("Please enter a valid integer for sampling steps.")

    while True:
        try:
            width = int(input("Enter the image width (default 512): ").strip() or 512)
            break
        except ValueError:
            print("Please enter a valid integer for width.")

    while True:
        try:
            height = int(input("Enter the image height (default 768): ").strip() or 768)
            break
        except ValueError:
            print("Please enter a valid integer for height.")

    while True:
        try:
            cfg_scale = float(input("Enter the CFG scale (default 7.5): ").strip() or 7.5)
            break
        except ValueError:
            print("Please enter a valid float for CFG scale.")

    while True:
        try:
            seed_input = input("Enter the seed (enter '-1' for random, default -1): ").strip() or "-1"
            seed = int(seed_input)
            break
        except ValueError:
            print("Please enter a valid integer for seed.")

    # Ask for global number of images and iterations
    while True:
        try:
            num_images = int(input("Enter the number of images to generate per iteration (default 1): ").strip() or 1)
            if num_images > 0:
                break
            else:
                print("Number of images must be positive.")
        except ValueError:
            print("Please enter a valid integer for number of images.")

    while True:
        try:
            num_iterations = int(input("Enter the number of iterations (default 1): ").strip() or 1)
            if num_iterations > 0:
                break
            else:
                print("Number of iterations must be positive.")
        except ValueError:
            print("Please enter a valid integer for number of iterations.")

    # Create settings dictionary
    settings = {
        "model": model,
        "sampling_method": sampling_method,
        "scheduler": scheduler,
        "sampling_steps": sampling_steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "api_endpoint": api_endpoint
    }

    # Process each selected folder
    for story_name in selected_folders:
        folder_path = os.path.join(input_dir, story_name)
        print(f"\nProcessing folder: {story_name}")

        # Output folder for this story
        story_output_dir = os.path.join(output_dir, story_name)

        # Process prompts and generate JSON files
        print("\nProcessing character prompts...")
        character_prompts = create_prompts('character', folder_path)
        if not character_prompts:
            print("No character prompts found. Skipping character image generation.")
        else:
            character_json_files = generate_json_files(character_prompts, 'character', story_name, settings['seed'], num_images, num_iterations, output_dir)

        print("\nProcessing scene prompts...")
        scene_prompts = create_prompts('scene', folder_path)
        if not scene_prompts:
            print("No scene prompts found. Skipping scene image generation.")
        else:
            scene_json_files = generate_json_files(scene_prompts, 'scene', story_name, settings['seed'], num_images, num_iterations, output_dir)

        print("\nJSON files for characters and scenes have been created.")
        print("You can review and edit them before proceeding if needed.")

        # Start keyboard listener
        print("Press 'F8' at any time to pause/resume the script during image generation.")
        start_keyboard_listener()

        # Generate images for characters
        if character_prompts:
            print("\nStarting image generation for characters...")
            generate_images(settings, 'character', story_name, num_images, num_iterations, output_dir, character_prompts, selected_loras, lora_dir)
        else:
            print("No character prompts to process.")

        # Generate images for scenes
        if scene_prompts:
            print("\nStarting image generation for scenes...")
            generate_images(settings, 'scene', story_name, num_images, num_iterations, output_dir, scene_prompts, selected_loras, lora_dir)
        else:
            print("No scene prompts to process.")

        # Stop keyboard listener after image generation
        stop_keyboard_listener()

        print(f"\nImage generation completed for folder: {story_name}")

if __name__ == '__main__':
    main()
