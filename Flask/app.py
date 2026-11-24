import re
from datetime import datetime
from html import unescape

from flask import Flask, redirect, render_template, request, url_for
from markupsafe import Markup

import utils
from model import ImageUploadError, decode_image, is_leaf, predict_image

MAX_IMAGE_BYTES = 10 * 1024 * 1024
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_BYTES + 64 * 1024

CROPS = [
    "Apple", "Blueberry", "Cherry", "Corn", "Grape", "Orange", "Peach",
    "Pepper", "Potato", "Raspberry", "Soybean", "Squash", "Strawberry", "Tomato",
]

_BR = re.compile(r'<br\s*/?>', re.I)
_TAG = re.compile(r'<[^>]+>')
_LIST_NUMBER = re.compile(r'^\s*\d{1,2}\s*[.)](?!\d)\s*')

def _clean(text):
    return re.sub(r'\s+', ' ', unescape(_TAG.sub('', text))).strip()

def _dedupe(items):
    seen, result = set(), []
    for item in items:
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result

def parse_report(raw):
    """Turn the stored HTML snippet for a prediction into structured data."""
    lines = [_clean(part) for part in _BR.split(raw)]
    lines = [line for line in lines if line]
    crop = disease = None
    section = None
    intro, cause, steps = [], [], []
    for line in lines:
        lowered = line.lower()
        if section is None and crop is None and lowered.startswith('crop') and ':' in line:
            crop = line.split(':', 1)[1].strip()
        elif section is None and disease is None and lowered.startswith('disease') and ':' in line:
            disease = line.split(':', 1)[1].strip()
        elif lowered.startswith('cause of disease'):
            section = 'cause'
        elif lowered.startswith('how to prevent'):
            section = 'steps'
        elif section == 'cause':
            cause.append(_LIST_NUMBER.sub('', line))
        elif section == 'steps':
            steps.append(_LIST_NUMBER.sub('', line))
        elif section is None and disease is not None:
            intro.append(line)
    if not crop or not disease:
        return None
    return {
        'crop': re.sub(r'(?<=\w)\(', ' (', crop),
        'disease': disease,
        'healthy': disease.lower().startswith('no disease'),
        'intro': _dedupe(intro),
        'cause': _dedupe(cause),
        'steps': _dedupe(steps),
    }

def show_message(title, message, status=200, retry=True):
    return render_template("display.html", title=title, message=message, report=None, retry=retry), status

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', crops=CROPS)

@app.errorhandler(413)
def upload_too_large(_error):
    return show_message("Image is too large", "Choose a photo smaller than 10 MB.", 413)

@app.errorhandler(404)
def not_found(_error):
    return show_message("Page not found", "We couldn't find the page you were looking for.", 404, retry=False)

@app.errorhandler(500)
def server_error(_error):
    return show_message("Something went wrong", "Please try again in a moment.", 500, retry=False)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == "GET":
        return redirect(url_for("home", _anchor="detect"))
    file = request.files.get("file")
    if not file or not file.filename:
        return show_message("No image uploaded", "Choose a leaf photo and try again.", 400)
    data = file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        return upload_too_large(None)
    try:
        image = decode_image(data)
    except ImageUploadError as error:
        return show_message("Image could not be read", str(error), 400)
    if not is_leaf(image):
        return show_message(
            "Could not verify a leaf",
            "Upload a color close-up of one leaf, with the whole leaf visible against a plain background.",
            422,
        )
    prediction = predict_image(image)
    if prediction is None:
        return show_message(
            "Prediction uncertain",
            "The crop or disease is unclear. Try a sharp, well-lit photo of one leaf with any spots or damage visible.",
        )
    raw = utils.disease_dic[prediction]
    report = parse_report(raw)
    if report is None:
        return show_message("Analysis result", Markup(raw).striptags())
    return render_template("display.html", title="Analysis result", report=report, message=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)
