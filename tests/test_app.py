import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Flask'))
from app import app
from model import num_classes, decode_image, predict_image
import utils

class SmokeTests(unittest.TestCase):
    def test_home(self):
        self.assertEqual(app.test_client().get('/').status_code, 200)

    def test_missing_upload(self):
        self.assertEqual(app.test_client().post('/predict').status_code, 400)

    def test_invalid_upload(self):
        response = app.test_client().post('/predict', data={'file': (io.BytesIO(b'invalid'), 'bad.jpg')})
        self.assertEqual(response.status_code, 400)

    def test_model_labels(self):
        self.assertEqual(len(num_classes), 38)
        self.assertTrue(set(num_classes).issubset(utils.disease_dic))

    def test_prediction(self):
        image = decode_image((ROOT / 'test_images/apple_healthy.JPG').read_bytes())
        self.assertIn(predict_image(image), [None, *num_classes])
