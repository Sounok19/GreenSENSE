# GreenSENSE — Plant Disease Identification

GreenSENSE is a Flask web application using a PyTorch ResNet-34 model to identify plant leaf diseases and healthy leaves across 38 classes and 14 crop groups.

## Features

- Leaf verification before classification.
- Five-view inference with confidence, margin and agreement checks.
- Image cropping and upload interface with a 10 MB limit.
- CPU inference with trained weights.

## Repository status

Initial deployment configuration is committed. The complete application source, assets and trained model weights must still be uploaded from the prepared project archive before the application can run. Model weights are tracked with Git LFS.

## Local setup (after uploading the complete project)

```bash
python -m pip install -r requirements.txt
python Flask/app.py
```

Visit http://localhost:7860. The Dockerfile supports deployment on port 7860.

Predictions are not a substitute for expert agricultural diagnosis. No independently verified accuracy claim is made. No license has been specified.
