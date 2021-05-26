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

#开操作
kernel = np.ones((20, 20), np.uint8)
img_opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
# addWeighted: dst = src1*alpha + src2*beta + gamma;
img_opening = cv2.addWeighted(img, 1, img_opening, -1, 0)

# Canny边缘检测
ret, img_thresh = cv2.threshold(img_opening, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
img_edge = cv2.Canny(img_thresh, 100, 200)

# 先闭后开运算
kernel = np.ones((cfg['morphologyr'], cfg['morphologyc']), np.uint8)
img_edge = cv2.morphologyEx(img_edge, cv2.MORPH_CLOSE, kernel)
img_edge = cv2.morphologyEx(img_edge, cv2.MORPH_OPEN, kernel)

contours, _ = cv2.findContours(img_edge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
# 筛选可能的区域轮廓
car_contours = []
for contour in contours:
	# rect: ((center), (w, h), angle)
	rect = cv2.minAreaRect(contour)
	rw, rh = rect[1]
	ratio = rh / rw
	# 长宽比例约为2~5.5的比较可能为车牌
	if 2 < ratio < 5.5:
		car_contours.append(contour)
		contour_img = cv2.drawContours(oldimg, contour, -1, color=(0, 0, 255), )
imshow(contour_img)











