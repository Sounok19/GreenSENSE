---
title: GreenSENSE
emoji: 🌿
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# GreenSENSE — Plant Disease Identification

GreenSENSE is a Flask web application that uses a PyTorch ResNet-34 model to identify plant leaf diseases and healthy leaves across 38 classes and 14 crop groups. Upload a leaf photo to receive a prediction, an explanation of the condition and prevention guidance where available.

## Features

- Leaf verification before classification, with rejection of unsuitable images.
- Five-view inference and confidence, margin and agreement checks to reject uncertain predictions.
- Image cropping and upload interface, with a 10 MB upload limit.
- CPU inference with supplied trained weights; no training required to run the app.

## Project structure

```text
Flask/                 Web application, model, templates, static assets
  Models/              ResNet-34 checkpoint and leaf detector parameters
Src/                   Original Colab training notebook
test_images/          Example leaf photographs
Dockerfile             Docker / Hugging Face Spaces runtime
requirements.txt       Python runtime dependencies
tests/                Smoke tests
```

## Run locally (Python 3.11)

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python Flask/app.py
```

Visit http://localhost:7860. Alternatively use Docker:

```bash
docker build -t greensense .
docker run --rm -p 7860:7860 greensense
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for GitHub and Hugging Face Spaces instructions. The Docker Space serves the original Flask UI on port 7860. The model files are tracked with Git LFS.

## Training and limitations

The original training notebook is retained for reference. It expects a separate dataset in Google Drive, which is not included. Predictions are not a substitute for expert agricultural diagnosis. Field images may differ from training images. No independently verified accuracy claim is made here. The original archive did not specify a license; confirm rights to redistribute the code, weights, images and disease descriptions before publishing publicly.
