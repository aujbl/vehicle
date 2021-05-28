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
oldimg = img
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
# 画出轮廓的最小外接矩形，根据外接矩形的长宽比筛选可能的区域，长宽比在2~5之间是可能存在车牌的区域
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

# # 对可能的区域进行旋转调整和扩大范围
# car_imgs = []
# for rect in car_rects:
# 	box = cv2.boxPoints(rect)
# 	w, h = rect[1]
# 	extraX = 5
# 	extraY = 10
# 	imgWidth, imgHeight = img.shape
# 	if w > h:  # 宽大于高，顺时针旋转
# 		width, height = w, h
# 		M = cv2.cv2.getRotationMatrix2D((box[0][0], box[0][1]), rect[2], 1)
# 		rect_img = cv2.warpAffine(oldimg, M, (oldimg.shape[0], oldimg.shape[1]))
# 		imshow(rect_img)
# 		# 扩大范围
# 		if int(box[0][0]) - extraX < 0:
# 			minX = 0
# 		else:
# 			minX = int(box[0][0]) - extraX
#
# 		if int(box[0][0]) + int(width) + extraX > imgWidth + 99:
# 			maxX = imgWidth + 99
# 		else:
# 			maxX = int(box[0][0]) + int(width) + extraX
#
# 		if int(box[0][1]) - int(height) - extraY < 0:
# 			minY = 0
# 		else:
# 			minY = int(box[0][1]) - int(height) - extraY
#
# 		if int(box[0][1]) + extraY > imgHeight + 99:
# 			maxY = imgHeight + 99
# 		else:
# 			maxY = int(box[0][1]) + extraY
#
# 	else:  # 宽小于高，逆时针旋转
# 		width, height = h, w
# 		M = cv2.cv2.getRotationMatrix2D((box[0][0], box[0][1]), rect[2], 1)
# 		rect_img = cv2.warpAffine(oldimg, M, (oldimg.shape[1], oldimg.shape[0]))
# 		imshow(rect_img)
# 		# 扩大范围
# 		if int(box[0][0]) - extraX < 0:
# 			minX = 0
# 		else:
# 			minX = int(box[0][0]) - extraX
#
# 		if int(box[0][0]) + int(width) + extraX > imgWidth + 99:
# 			maxX = imgWidth + 99
# 		else:
# 			maxX = int(box[0][0]) + int(width) + extraX
#
# 		if int(box[0][1]) - extraY < 0:
# 			minY = 0
# 		else:
# 			minY = int(box[0][1]) - extraY
#
# 		if int(box[0][1]) + int(height) + extraY > imgHeight + 99:
# 			maxY = imgHeight + 99
# 		else:
# 			maxY = int(box[0][1]) + int(height) + extraY
#
# 	rect_img = rect_img[minY:maxY, minX:maxX]
# 	imshow(rect_img)
# 	car_imgs.append(rect_img)

card_imgs = []
# 矩形区域可能是倾斜的矩形
for rect in car_rects:
	angle = 1 if -1 < rect[2] < 1 else rect[2]
	# 扩大rect范围，避免车牌边缘被排除
	# rect = (rect[0], (rect[1][0] + 5, rect[1][1] + 5), angle)
	'''
	.................*(top).................... - - >
	| ........*(left)..*.......................
	| .........*........*(right)..............
	v ..........*(low).........................
	左：x坐标最小，右：x坐标最大，顶：y坐标最小，底：y坐标最大
	'''
	box = cv2.boxPoints(rect)
	box = np.int0(box)
	contour_img = cv2.drawContours(oldimg, [box], 0, (0, 0, 255), 2)
	imshow(contour_img)

	# # 按第一列排序
	# box = box[np.lexsort(box[:, ::-1].T)]
	# left_point, right_point = box[0], box[-1]
	# # 按最后一列排序
	# box = box[np.lexsort(box.T)]
	# height_point, low_point = box[0], box[-1]
	#
	# if left_point[1] <= right_point[1]:  # 正角度
	# 	new_right_point = [right_point[0], height_point[1]]
	# 	pts2 = np.float32([left_point, height_point, new_right_point])  # 字符只是高度需要改变
	# 	pts1 = np.float32([left_point, height_point, right_point])
	# 	M = cv2.getAffineTransform(pts1, pts2)  # 仿射变换
	# 	dst = cv2.warpAffine(oldimg, M, (pic_width, pic_height))
	# 	point_limit(new_right_point)
	# 	point_limit(height_point)
	# 	point_limit(left_point)
	# 	card_img = dst[int(left_point[1]):int(height_point[1]), int(left_point[0]):int(new_right_point[0])]
	# 	card_imgs.append(card_img)
	# elif left_point[1] > right_point[1]:  # 负角度
	# 	new_left_point = [left_point[0], height_point[1]]
	# 	pts2 = np.float32([new_left_point, height_point, right_point])  # 字符只是高度需要改变
	# 	pts1 = np.float32([left_point, height_point, right_point])
	# 	M = cv2.getAffineTransform(pts1, pts2)
	# 	dst = cv2.warpAffine(oldimg, M, (pic_width, pic_height))
	# 	point_limit(right_point)
	# 	point_limit(height_point)
	# 	point_limit(new_left_point)
	# 	card_img = dst[int(right_point[1]):int(height_point[1]), int(new_left_point[0]):int(right_point[0])]
	# 	card_imgs.append(card_img)
	# imshow(card_img)










