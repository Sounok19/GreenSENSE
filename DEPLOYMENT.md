# Publish GreenSENSE

Install Git and Git LFS (https://git-lfs.com/). Extract the ZIP and open a terminal in the directory containing README.md. The following commands assume new empty repositories and authenticated accounts. Do not use force push against existing projects.

## GitHub

Create an empty repository named `GreenSENSE` at https://github.com/new (no README, license or gitignore). Choose visibility after checking redistribution rights. Run:

```bash
git lfs install
git init -b main
git add .
git commit -m "Initial GreenSENSE release"
git remote add origin https://github.com/YOUR_USERNAME/GreenSENSE.git
git push -u origin main
```

Authenticate through Git Credential Manager or GitHub CLI, not by embedding tokens in source code.

## Hugging Face Spaces

Create a Space at https://huggingface.co/new-space named `GreenSENSE`, choose Docker SDK, Blank template, and CPU hardware. Install the Hugging Face CLI (`pip install -U huggingface_hub`) and authenticate using `hf auth login` with a token permitted to write to the Space.

From the extracted project directory run:

```bash
hf upload YOUR_HF_USERNAME/GreenSENSE . --repo-type space --exclude '.git/**' '.venv/**' '**/__pycache__/**'
```

This uploads the source and weights to the Space; Docker builds automatically. Check the build and runtime logs, then test a sample image. The README metadata and Dockerfile are already configured for port 7860. Update the GitHub README with the actual Space URL after successful deployment.

## Smoke tests

```bash
python -m unittest discover -s tests -v
```
