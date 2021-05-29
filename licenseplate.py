import cv2
import numpy as np
from numpy.linalg import norm
import sys
import os
import json
from matplotlib import pyplot as plt

SZ = 20          # 训练图片长宽
MAX_WIDTH = 1000 # 原始图片最大宽度
Min_Area = 2000  # 车牌区域允许最大面积
PROVINCE_START = 1000

def imshow(img, name='img'):
	cv2.imshow(name, img)
	cv2.waitKey(0)

def point_limit(point):
	if point[0] < 0:
		point[0] = 0
	if point[1] < 0:
		point[1] = 0

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

blur = 5
img = cv2.GaussianBlur(img, (blur, blur), 0)
old_img = img
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# #开操作
# k = 9
# kernel = np.ones((k, k), np.uint8)
# img_opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
# imshow(img_opening)
# # addWeighted: dst = src1*alpha + src2*beta + gamma;
# img_opening = cv2.addWeighted(img, 1, img_opening, -1, 0)
# imshow(img_opening)

# Canny边缘检测
ret, img_thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
img_edge = cv2.Canny(img_thresh, 100, 200)

# 先闭后开运算
kernel_size = (7, 20)
# kernel = np.ones((cfg['morphologyr'], cfg['morphologyc']), np.uint8)
kernel = np.ones(kernel_size, np.uint8)
img_edge = cv2.morphologyEx(img_edge, cv2.MORPH_CLOSE, kernel)
img_edge = cv2.morphologyEx(img_edge, cv2.MORPH_OPEN, kernel)

contours, _ = cv2.findContours(img_edge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
# 画出轮廓的最小外接矩形，根据外接矩形的长宽比筛选可能的区域，长宽比在2~5.5之间是可能存在车牌的区域
car_rects = []
for contour in contours:
	# rect: ((center), (w, h), angle)
	rect = cv2.minAreaRect(contour)
	rw, rh = rect[1]
	ratio = rh / rw if rh > rw else rw / rh
	# 长宽比例约为2~5.5的比较可能为车牌
	if 2 < ratio < 5.5:
		car_rects.append(rect)
		# rect = (rect[0], (rect[1][0]+3, rect[1][1]+3), rect[2])
# 		box = cv2.boxPoints(rect)
# 		box = np.int0(box)
# 		contour_img = cv2.drawContours(oldimg, [box], 0, (0, 0, 255), 2)
# imshow(contour_img)

car_imgs = []
# 将向不同角度倾斜的矩形调整为水平，并截取下来
for rect in car_rects:
	'''测试候选框调整结果'''
	# box = cv2.boxPoints(rect)
	# box = np.int0(box)
	# oldimg = cv2.drawContours(oldimg, [box], 0, (0, 0, 255), 2)
	(cen_x, cen_y), (w, h), angle = rect
	angle = angle if w > h else angle + 90
	if w < h:
		w, h = h, w
	left, right = int(cen_x - w / 2), int(cen_x + w / 2)
	up, down = int(cen_y - h / 2), int(cen_y + h / 2)
	if angle % 90 == 0:
		rotate_img = old_img
	else:
		M = cv2.getRotationMatrix2D((cen_x, cen_y), angle, 1)
		rotate_img = cv2.warpAffine(old_img, M, (old_img.shape[1], old_img.shape[0]))
	car_img = rotate_img[up:down, left:right]
	car_imgs.append(car_img)
	'''测试候选框调整结果'''
	# plt.figure()
	# plt.subplot(1, 3, 1)
	# plt.imshow(oldimg)
	# plt.subplot(1, 3, 2)
	# plt.imshow(rotate_img)
	# plt.subplot(1, 3, 3)
	# plt.imshow(car_img)
	# plt.show()

	'''
	.................*(top).................... - - >
	| ........*(left)..*.......................
	| .........*........*(right)..............
	v ..........*(low).........................
	左：x坐标最小，右：x坐标最大，顶：y坐标最小，底：y坐标最大
	'''
	# # 按第一列排序
	# box = box[np.lexsort(box[:, ::-1].T)]
	# left_point, right_point = box[0], box[-1]
	# # 按最后一列排序
	# box = box[np.lexsort(box.T)]
	# height_point, low_point = box[0], box[-1]






