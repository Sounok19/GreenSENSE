import io
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
import torch
import torch.nn as nn
from torch.nn import functional as F
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.transforms import functional as TF

class Plant_Disease_Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = models.resnet34(weights=None)
        num_ftrs = self.network.fc.in_features
        self.network.fc = nn.Linear(num_ftrs, 38)

    def forward(self, xb):
        out = self.network(xb)
        return out

transform = transforms.Compose(
    [transforms.Resize(size=128),
     transforms.ToTensor()])

num_classes = ['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy', 'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
               'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy']

models_dir = Path(__file__).resolve().parent / "Models"
model = Plant_Disease_Model()
model.load_state_dict(torch.load(
    models_dir / "plantDisease-resnet34.pth", map_location="cpu", weights_only=True))
model.eval()

with (models_dir / "leaf-detector.json").open(encoding="utf-8") as weights_file:
    leaf_detector = json.load(weights_file)
leaf_weights = torch.tensor(leaf_detector["weights"])
leaf_bias = leaf_detector["bias"]

MIN_LEAF_SCORE = 0.05
MIN_DISEASE_SCORE = 0.40
MIN_DISEASE_MARGIN = 0.10
MAX_IMAGE_PIXELS = 24_000_000

class ImageUploadError(ValueError):
    pass

def decode_image(data):
    try:
        with Image.open(io.BytesIO(data)) as source:
            width, height = source.size
            if min(width, height) < 32 or width * height > MAX_IMAGE_PIXELS:
                raise ImageUploadError("Use an image at least 32 pixels wide and tall and under 24 megapixels.")
            if max(width, height) > 8 * min(width, height):
                raise ImageUploadError("Choose a photo with the whole leaf in a standard portrait or landscape frame.")
            image = ImageOps.exif_transpose(source).convert("RGB")
    except ImageUploadError:
        raise
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as error:
        raise ImageUploadError("Choose a readable image, such as a JPG or PNG under 24 megapixels.") from error
    image.thumbnail((768, 768), Image.Resampling.BILINEAR)
    return image

@torch.inference_mode()
def is_leaf(image):
    square = image.resize((32, 32), Image.Resampling.BILINEAR)
    if all(high - low < 5 for low, high in square.getextrema()):
        return False
    pixels = TF.to_tensor(square)
    chroma = pixels.amax(dim=0) - pixels.amin(dim=0)
    if (chroma >= 8 / 255).float().mean().item() < 0.05:
        return False
    batch = F.interpolate(pixels.unsqueeze(0), size=(128, 128), mode="bilinear", align_corners=False)
    network = model.network
    x = network.maxpool(network.relu(network.bn1(network.conv1(batch))))
    x = network.layer2(network.layer1(x))
    middle = network.layer3(x)
    high = network.layer4(middle)
    features = torch.cat((F.normalize(middle.mean((2, 3))), F.normalize(high.mean((2, 3)))), dim=1)
    score = (features @ leaf_weights + leaf_bias).sigmoid().item()
    return score >= MIN_LEAF_SCORE

@torch.inference_mode()
def predict_image(image):
    width, height = image.size
    inset_x, inset_y = width // 16, height // 16
    center = image.crop((inset_x, inset_y, width - inset_x, height - inset_y))
    center = center.resize(image.size, Image.Resampling.BILINEAR)
    views = (image, ImageOps.mirror(image), ImageOps.flip(image), center,
             ImageEnhance.Brightness(image).enhance(0.82))
    probabilities = model(torch.stack([transform(view) for view in views])).softmax(dim=1)
    scores, labels = probabilities.mean(dim=0).topk(2)
    best = labels[0]
    votes = (probabilities.argmax(dim=1) == best).sum()
    if scores[0] < MIN_DISEASE_SCORE or scores[0] - scores[1] < MIN_DISEASE_MARGIN or votes < 3:
        return None
    return num_classes[best.item()]
