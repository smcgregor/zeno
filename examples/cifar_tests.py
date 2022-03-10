import PIL
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import torchvision.transforms as transforms
from zeno import load_data, load_model, metric, slicer, transform, preprocess

transform_image = transforms.Compose(
    [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
)


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)  # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


classes = (
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
)


def get_brightness(im):
    im_grey = im.convert("LA")  # convert to grayscale
    width, height = im.size

    total = 0
    for i in range(0, width):
        for j in range(0, height):
            total += im_grey.getpixel((i, j))[0]

    return total / (width * height)


@preprocess
def brightness(images):
    return [get_brightness(im) for im in images]


# Return a prediction function that returns output given input
@load_model
def load_model(model_path):
    net = Net()
    net.load_state_dict(torch.load(model_path))

    def pred(instances):
        imgs = torch.stack([transform_image(img) for img in instances])
        with torch.no_grad():
            out = net(imgs)
        return [classes[i] for i in torch.argmax(out, dim=1).detach().numpy()]

    return pred


@load_data
def load_data(df_metadata, id_col, data_path):
    return [PIL.Image.open(os.path.join(data_path, img)) for img in df_metadata[id_col]]


@slicer(["accuracy"])
def overall(metadata):
    return metadata.index


@slicer(["accuracy"])
def low_brightness(metadata):
    return metadata[metadata["brightness"] < 80].index


# @slicer(["accuracy", ("rotate", "accuracy")])
# def medium_sample(metadata):
#     return metadata.sample(100).index


@slicer(["accuracy"])
def by_class(metadata, label_col):
    return [(c, metadata[metadata[label_col] == c].index) for c in classes]


# @transform
# def rotate(data, metadata):
#     return [img.rotate(90, PIL.Image.NEAREST, expand=1) for img in data], metadata


@metric
def accuracy(output, metadata, label_col):
    return metadata[label_col] == output
