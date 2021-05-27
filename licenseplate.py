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

def point_limit(point):
	if point[0] < 0:
		point[0] = 0
	if point[1] < 0:
		point[1] = 0

pic_file = './test_img/yellow.jpg'
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
k = 7
kernel = np.ones((k, k), np.uint8)
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
		box = cv2.boxPoints(rect)
		box = np.int0(box)
		contour_img = cv2.drawContours(oldimg, [box], 0, (0, 0, 255), 2)
imshow(contour_img)
#
# card_imgs = []
# # 矩形区域可能是倾斜的矩形
# for rect in car_rects:
# 	angle = 1 if -1 < rect[2] < 1 else rect[2]
# 	# 扩大rect范围，避免车牌边缘被排除
# 	rect = (rect[0], (rect[1][0] + 5, rect[1][1] + 5), angle)
#
# 	box = cv2.boxPoints(rect)
# 	# 避免边界超出图像边界
# 	height_point = right_point = [0, 0]
# 	left_point = low_point = [pic_width, pic_height]
# 	for point in box:
# 		if left_point[0] > point[0]:
# 			left_point = point
# 		if low_point[1] > point[1]:
# 			low_point = point
# 		if height_point[1] < point[1]:
# 			height_point_point = point
# 		if right_point[0] < point[0]:
# 			right_point = point
#
# 	if left_point[1] <= right_point[1]:  # 正角度
# 		new_right_point = [right_point[0], height_point[1]]
# 		pts2 = np.float32([left_point, height_point, new_right_point])  # 字符只是高度需要改变
# 		pts1 = np.float32([left_point, height_point, right_point])
# 		M = cv2.getAffineTransform(pts1, pts2)  # 仿射变换
# 		dst = cv2.warpAffine(oldimg, M, (pic_width, pic_height))
# 		point_limit(new_right_point)
# 		point_limit(height_point)
# 		point_limit(left_point)
# 		card_img = dst[int(left_point[1]):int(height_point[1]), int(left_point[0]):int(new_right_point[0])]
# 		card_imgs.append(card_img)
# 	# cv2.imshow("card", card_img)
# 	# cv2.waitKey(0)
# 	elif left_point[1] > right_point[1]:  # 负角度
#
# 		new_left_point = [left_point[0], height_point[1]]
# 		pts2 = np.float32([new_left_point, height_point, right_point])  # 字符只是高度需要改变
# 		pts1 = np.float32([left_point, height_point, right_point])
# 		M = cv2.getAffineTransform(pts1, pts2)
# 		dst = cv2.warpAffine(oldimg, M, (pic_width, pic_height))
# 		point_limit(right_point)
# 		point_limit(height_point)
# 		point_limit(new_left_point)
# 		card_img = dst[int(right_point[1]):int(height_point[1]), int(new_left_point[0]):int(right_point[0])]
# 		card_imgs.append(card_img)
# # cv2.imshow("card", card_img)
# # cv2.waitKey(0)









