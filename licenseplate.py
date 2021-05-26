import cv2
import numpy as np
from numpy.linalg import norm
import sys
import os
import json

SZ = 20          # 训练图片长宽
MAX_WIDTH = 1000 # 原始图片最大宽度
Min_Area = 2000  # 车牌区域允许最大面积
PROVINCE_START = 1000

def imshow(img, name='img'):
	cv2.imshow(name, img)
	cv2.waitKey(0)

pic_file = './test_img/green.jpg'
img = cv2.imread(pic_file)
pic_height, pic_width = img.shape[:2]

f = open('config.js')
j = json.load(f)
for c in j["config"]:
	if c["open"]:
		cfg = c.copy()
		break
	else:
		raise RuntimeError('[ ERROR ] 没有设置有效配置参数.')

blur = 3
img = cv2.GaussianBlur(img, (blur, blur), 0)
oldimg = img
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
imshow(img)

kernal = np.ones((10, 10), np.uint8)
img_opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernal)
imshow(img_opening)











