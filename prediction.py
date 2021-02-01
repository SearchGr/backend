import io

import requests
import torch
import torchvision
from PIL import Image
from torch.nn import functional
from torchvision import models
from torchvision import transforms

import app_properties

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
detector = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True, min_size=800)
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
    indices = output[0]['labels'][prediction_scores >= app_properties.detection_threshold]

    result_set = set()
    for label in indices:
        result_set.add(label.item())
    result = list(result_set)
    return result


def get_classifications(url):
    image = prepare_image(url, classification_transforms)
    result = classifier(image)
    _, index = torch.max(result, 1)

    percentages = functional.softmax(result, dim=1)[0] * 100
    _, indices = torch.sort(result, descending=True)

    i = 0
    result = []
    while indices[0][i]:
        if percentages[indices[0][i]].item() > app_properties.classification_threshold * 100:
            result.append(indices[0][i].item())
        i += 1
    return result


def prepare_image(url, transformations):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)
    image = transformations(Image.open(image_bytes))
    return image.unsqueeze(0)
