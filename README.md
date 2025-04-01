# StableDiffusion-Automator-v1.3

## Overview

StableDiffusion-Automator-v1.3 is an advanced automation tool designed to streamline the process of generating AI-generated images based on structured narratives. By leveraging **Stable Diffusion**, this tool enables users to automate the creation of visual content from text-based descriptions, making it an invaluable resource for **YouTube video creators, AI researchers, and storytellers**. 

This project is particularly beneficial for:
- **Content creators** who need to generate AI-generated illustrations for their videos.
- **Researchers** looking to study AI-driven storytelling.
- **Automation enthusiasts** interested in procedural image generation.

## Features

- **Automated Scene-to-Image Generation**: Convert structured text descriptions into AI-generated scenes.
- **Story-Based Processing**: Process entire scripts to generate a sequence of images for **video storytelling**.
- **Character Consistency**: Maintain character appearance across multiple scenes.
- **Batch Processing**: Generate multiple images automatically without manual intervention.
- **Flexible Customization**: Modify prompt structures, control outputs, and tweak settings for optimized results.

## Folder Structure

```
StableDiffusion-Automator-v1.3/
│-- input/
│   ├── scripts/                  # Story scripts (scene descriptions)
│   ├── templates/                # Predefined formats for scene and character templates
│   ├── three_christs/            # Example structured data (Three Christs of Ypsilanti)
│-- output/                        # Generated images
│-- settings/
│   ├── config.json                # Main configuration file
│   ├── stable_diffusion_options.json  # Model settings
│-- main.py                        # Script to start the automation process
│-- requirements.txt               # Required Python dependencies
│-- README.md                      # This file
```

## Installation

### Prerequisites

Ensure you have the following installed before running the project:

- **Python 3.7+**: Download from [Python.org](https://www.python.org/downloads/).
- **Stable Diffusion**: This project relies on an installed and running Stable Diffusion instance.
- **Pip (Python Package Installer)**: If not installed, run:
  ```sh
  python -m ensurepip --default-pip
  ```

### Install Dependencies

After cloning the repository, navigate to the project folder and install the required dependencies:

```sh
git clone https://github.com/Neverlow512/StableDiffusion-Automator-v1.3.git
cd StableDiffusion-Automator-v1.3
pip install -r requirements.txt
```

### Setup Configuration

Modify the `config.json` and `stable_diffusion_options.json` in the `settings/` folder to match your requirements.

## Usage

### Step 1: Prepare Your Story Script

1. Write a **structured script** detailing scenes and characters.
2. Use the provided **templates** to format scene descriptions properly.
3. Place the script inside the `input/scripts/` directory.

### Step 2: Define Scene and Character Details

- **Scene Templates**: `input/templates/scenes_template.txt`
- **Character Templates**: `input/templates/characters_template.txt`

Each scene should have a **textual description** that Stable Diffusion can interpret, for example:

```txt
Scene 1: A dimly lit interrogation room, metal table at the center, detective standing in the shadows.
```

### Step 3: Run the Automation

To start the scene generation process, run:
```sh
python main.py
```

The script will process the input, generate images for each scene, and save them inside the `output/` folder.

## Example Use Case: "Three Christs of Ypsilanti"

Inside the `three_christs/` folder, we provide an example scenario based on the famous psychological case study **"Three Christs of Ypsilanti"**, where three patients all believed they were Jesus Christ. 

This structured example demonstrates how to:
- Maintain character consistency across multiple generated scenes.
- Automate the creation of **story-based AI-generated illustrations**.
- Explore psychological case studies visually with AI-generated representations.

### Why is this Useful for Research?

- **Psychological Experiments**: Generate visual representations of psychological scenarios.
- **Historical Narratives**: Bring historical case studies to life through AI-generated imagery.
- **Ethical AI Studies**: Explore how AI-generated images interpret human-defined prompts.

## Advanced Configuration

Modify `settings/config.json` to tweak the automation process:
```json
{
  "resolution": "1024x1024",
  "sampling_steps": 28,
  "cfg_scale": 4.7,
  "scheduler": "DPM++ SDE",
  "batch_size": 4
}
```

- `resolution`: Image size (optimal: `1024x1024`).
- `sampling_steps`: Number of diffusion steps (higher = more detailed output).
- `cfg_scale`: Guidance scale for prompt adherence.
- `scheduler`: Sampling algorithm.
- `batch_size`: Number of images per scene.

## Troubleshooting

### Issue: No Images Are Generated
- Ensure Stable Diffusion is running and properly set up.
- Verify that scene scripts are formatted correctly.

### Issue: Poor Quality Images
- Increase `sampling_steps` in `config.json`.
- Adjust `cfg_scale` to find a balance between creativity and adherence.

### Issue: Characters Appear Inconsistent
- Use more **descriptive prompts** in `characters_template.txt`.

## Future Enhancements

- **GUI Integration**: Implement a graphical interface for easier script editing.
- **Multi-Model Support**: Extend support to alternative AI models (e.g., MidJourney, DALLE).
- **Audio-Narration**: Integrate TTS (Text-to-Speech) for generating narrated video sequences.

## License

This project is licensed under the MIT License. See the `LICENSE` file for full details.

## Contact

For questions, suggestions, or collaborations, reach out via:
- GitHub Issues: [Neverlow512](https://github.com/Neverlow512/)
- Email: neverlow512@proton.me

---

### Disclaimer

This tool is **strictly for research and educational purposes**. Ensure compliance with AI content guidelines and ethical considerations when using AI-generated media.
