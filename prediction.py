import io

import numpy
import requests
import torch
from PIL import Image
from torch.nn import functional
from torchvision import models
from torchvision import transforms

import app_properties

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
detector = models.detection.fasterrcnn_resnet50_fpn(pretrained=True, min_size=800)
detector.eval().to(device)

classifier = models.resnet101(pretrained=True)
classifier.eval().to(device)
classification_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )])


def get_detections(url):
    image = prepare_image(url, transforms.ToTensor())
    output = detector(image)
    prediction_scores = output[0]['scores'].detach().cpu().numpy()
    labels = output[0]['labels'][prediction_scores >= app_properties.DETECTION_THRESHOLD]
    return labels.unique().tolist()


def get_classifications(url):
    image = prepare_image(url, classification_transforms)
    result = classifier(image)
    percentages = functional.softmax(result, dim=1)[0].detach().numpy()
    return numpy.where(percentages > app_properties.CLASSIFICATION_THRESHOLD)[0].tolist()


def prepare_image(url, transformations):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)
    image = transformations(Image.open(image_bytes))
    return image.unsqueeze(0)
