# -*- coding: utf-8 -*-
from __future__ import division, print_function
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os


def plot_images(images):
    images = images[0:9]
    fig, axes = plt.subplots(3, 3)
    axes = np.ravel(axes)
    for i in range(len(images)):
        if len(images[i].shape) == 2:
            axes[i].imshow(images[i], cmap="gray")
        else:
            axes[i].imshow(images[i], interpolation="nearest")
        axes[i].set_xticks([])
        axes[i].set_yticks([])
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.show()


def get_next_image_loc(imgdir):
    for root, dirs, files in os.walk(imgdir):
        for name in files:
            path = os.path.join(root, name).split(os.path.sep)[::-1]
            yield (path[1], path[0])


def compute_edges(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (11, 11), 0)
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0)
    sobel_x = np.uint8(np.absolute(sobel_x))
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1)
    sobel_y = np.uint8(np.absolute(sobel_y))
    edged = cv2.bitwise_or(sobel_x, sobel_y)
    return edged    


def crop_image_to_edge(image, threshold=10, margin=0.2):
    edged = compute_edges(image)
    # find edge along center and crop
    mid_y = edged.shape[0] // 2
    notblack_x = np.where(edged[mid_y, :] >= threshold)[0]
    if notblack_x.shape[0] == 0:
        lb_x = 0
        ub_x = edged.shape[1]
    else:
        lb_x = notblack_x[0]
        ub_x = notblack_x[-1]
    if lb_x > margin * edged.shape[1]:
        lb_x = 0
    if (edged.shape[1] - ub_x) > margin * edged.shape[1]:
        ub_x = edged.shape[1]        
    mid_x = edged.shape[1] // 2
    notblack_y = np.where(edged[:, mid_x] >= threshold)[0]
    if notblack_y.shape[0] == 0:
        lb_y = 0
        ub_y = edged.shape[0]
    else:
        lb_y = notblack_y[0]
        ub_y = notblack_y[-1]
    if lb_y > margin * edged.shape[0]:
        lb_y = 0
    if (edged.shape[0] - ub_y) > margin * edged.shape[0]:
        ub_y = edged.shape[0]
    cropped = image[lb_y:ub_y, lb_x:ub_x, :]
    return cropped


def crop_image_to_aspect(image, tar=1.2):
    # load image
    image_bw = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # compute aspect ratio
    h, w = image_bw.shape[0], image_bw.shape[1]
    sar = h / w if h > w else w / h
    if sar < tar:
        return image
    else:
        k = 0.5 * (1.0 - (tar / sar))
        if h > w:
            lb = int(k * h)
            ub = h - lb
            cropped = image[lb:ub, :, :]
        else:
            lb = int(k * w)
            ub = w - lb
            cropped = image[:, lb:ub, :]
        return cropped
    

def brighten_image_hsv(image, global_mean_v):
    image_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(image_hsv)
    mean_v = int(np.mean(v))
    v = v - mean_v + global_mean_v
    image_hsv = cv2.merge((h, s, v))
    image_bright = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2RGB)
    return image_bright


def brighten_image_rgb(image, global_mean_rgb):
    r, g, b = cv2.split(image)
    m = np.array([np.mean(r), np.mean(g), np.mean(b)])
    brightened = image + global_mean_v - m
    return brightened
    

############################# main #############################

DATA_DIR = "../data/files/sample"
DATA_DIR2 = "../data/files/sample2"

# random sample for printing
sample_image_idxs = set(np.random.randint(0, high=1000, size=9).tolist())
sample_images = []

curr_idx = 0
vs = []
mean_rgbs = []
for image_dir, image_name in get_next_image_loc(DATA_DIR):
    if curr_idx % 100 == 0:
        print("Reading {:d} images".format(curr_idx))
    image = cv2.imread(os.path.join(DATA_DIR, image_dir, image_name))
    if curr_idx in sample_image_idxs:
        sample_images.append(image)
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(image_hsv)
    vs.append(np.mean(v))
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    r, g, b = cv2.split(image_rgb)
    mean_rgbs.append(np.array([np.mean(r), np.mean(g), np.mean(b)]))
    curr_idx += 1
print("Reading {:d} images, complete".format(curr_idx))    
global_mean_v = int(np.mean(np.array(vs)))
global_mean_rgbs = np.mean(mean_rgbs, axis=0)

# plot sample images at various steps
sample_images_rgb = [cv2.cvtColor(simg, cv2.COLOR_BGR2RGB) 
                for simg in sample_images]
plot_images(sample_images_rgb)
sample_cropped = [crop_image_to_aspect(simg) for simg in sample_images_rgb]
sample_resized = [cv2.resize(simg, (int(1.2 * 224), 224))
                for simg in sample_cropped]
plot_images(sample_resized)
sample_brightened_hsv = [brighten_image_hsv(simg, global_mean_v) 
                for simg in sample_resized]
plot_images(sample_brightened_hsv)
sample_brightened_rgb = [brighten_image_rgb(simg, global_mean_rgbs) 
                for simg in sample_resized]
plot_images(sample_brightened_rgb)

# save all images to disk
curr_idx = 0
for image_dir, image_name in get_next_image_loc(DATA_DIR):
    if curr_idx % 100 == 0:
        print("Writing {:d} preprocessed images".format(curr_idx))
    image = cv2.imread(os.path.join(DATA_DIR, image_dir, image_name))
    cropped = crop_image_to_aspect(image)
    resized = cv2.resize(cropped, (int(1.2 * 224), 224))
#    brightened = brighten_image_hsv(resized, global_mean_v)
    brightened = brighten_image_rgb(resized, global_mean_rgbs)
    plt.imsave(os.path.join(DATA_DIR2, image_dir, image_name), brightened)
    curr_idx += 1
print("Wrote {:d} images, complete".format(curr_idx))
