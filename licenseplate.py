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

'''注意OpenCV默认BGR，matplotlib默认RGB'''
def imshow(img, name='img'):
	cv2.imshow(name, img)
	cv2.waitKey(0)

pic_file = './test_img/green.jpg'
# pic_file = './test_img/blue.jpg'
# pic_file = './test_img/yellow.jpg'
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
# 		rect = (rect[0], (rect[1][0] + 3, rect[1][1] + 3), rect[2])
# 		box = cv2.boxPoints(rect)
# 		box = np.int0(box)
# 		contour_img = cv2.drawContours(old_img, [box], 0, (0, 0, 255), 2)
# imshow(contour_img)


car_imgs = []
# 将向不同角度倾斜的矩形调整为水平，并截取下来
for rect in car_rects:
	'''测试候选框调整结果'''
	# box = cv2.boxPoints(rect)
	# box = np.int0(box)
	# old_img = cv2.drawContours(old_img, [box], 0, (0, 0, 255), 2)
	(cen_x, cen_y), (w, h), angle = rect
	angle = angle if w > h else angle + 90
	if w < h:
		w, h = h, w
	left, right = int(cen_x - w / 2), int(cen_x + w / 2)
	up, down = int(cen_y - h / 2), int(cen_y + h / 2)
	# 可以考虑是否扩大矩形范围，以完整覆盖车牌区域
	extra_rows, extra_cols = int(0.05*(down-up)), int(0.05*(right-left))
	left, right = max(0, left-extra_cols), min(right+extra_cols, old_img.shape[1])
	up, down = max(0, up-extra_rows), min(down+extra_rows, old_img.shape[0])

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
	# plt.imshow(old_img)
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

limit_dict = {'yellow': [11, 34, 43, 46], 'green':  [35, 99, 43, 46], 'blue':   [100, 155, 43, 46]}

def fineMap(color, hsv_img):
	limit_H1, limit_H2, limit_S, limit_V = limit_dict[color]
	rows, cols = hsv_img.shape[:2]
	left, right, up, down = cols-1, 0, rows-1, 0
	# 绿牌上面是白边
	rows_limit = rows * 0.5 if color != 'green' else rows * 0.15
	cols_limit = cols * 0.3
	# 确定这一行是否属于车牌，最小的行为上边界，最大的行为下边界
	for i in range(rows):
		cnt = 0
		for j in range(cols):
			H, S, V = hsv_img[i][j]
			if limit_H1 <= H <= limit_H2 and S >= limit_S and V >= limit_V:
				cnt += 1
		if cnt > cols_limit:
			up, down = min(up, i), max(down, i)
	# 确定某一列是否属于车牌，最小为左边界，最大为右边界
	for j in range(cols):
		cnt = 0
		for i in range(rows):
			H, S, V = hsv_img[i][j]
			if limit_H1 <= H <= limit_H2 and S >= limit_S and V >= limit_V:
				cnt += 1
		if cnt > rows_limit:
			left, right = min(left, j), max(right, j)
	# 补上绿牌的白边
	if color == 'green':
		up = max(0, up - int(0.25*(down-up)))
	return left, right, up, down

colors = []
plates = []
for car_img in car_imgs:
	green = yellow = blue = 0
	hsv_img = cv2.cvtColor(car_img, cv2.COLOR_BGR2HSV)
	rows, cols = hsv_img.shape[:2]
	pixels = rows * cols

	for i in range(rows):
		for j in range(cols):
			H, S, V = hsv_img[i][j]
			if limit_dict['yellow'][0] <= H < limit_dict['yellow'][1] \
					and S >= limit_dict['yellow'][2] and V >= limit_dict['yellow'][3]:
				yellow += 1
			elif limit_dict['green'][0] <= H <= limit_dict['green'][1] \
					and S >= limit_dict['green'][2] and V >= limit_dict['green'][3]:
				green += 1
			elif limit_dict['blue'][0] <= H <= limit_dict['blue'][1] \
					and S >= limit_dict['blue'][2] and V >= limit_dict['blue'][3]:
				blue += 1
	max_color = max(yellow, green, blue)
	if max_color == yellow and 0.45 * pixels < yellow < 0.95 * pixels:
		color = 'yellow'
		# left, right, up, down = fineMap(color, hsv_img)
	elif max_color == blue and 0.45 * pixels < blue < 0.95 * pixels:
		color = 'blue'
		# left, right, up, down = fineMap(color, hsv_img)
	elif max_color == green and 0.35 * pixels < green < 0.95 * pixels:
		color = 'green'
	else:
		color = 'other'
	if color != 'other':
		left, right, up, down = fineMap(color, hsv_img)
		plate = car_img[up:down, left:right]
		colors.append(color)
		plates.append(plate)
	# 	print('rows: ', rows, 'cols: ', cols, 'color: ', color)
	# 	print('left: %d, right: %d, up: %d, down: %d' % (left, right, up, down), '\n')
	# 	plate = cv2.cvtColor(plate, cv2.COLOR_BGR2RGB)
	# 	plt.figure()
	# 	plt.imshow(plate)
	# 	plt.show()
	# else:
	# 	print('yellow/pixels:', yellow/pixels)
	# 	print('blue/pixels: ', blue/pixels)
	# 	print('green/pixels: ', green/pixels)

def findInterval(accumulation, intervalPre):
	min = 1  # 最小值
	for m in range(len(intervalPre)):
		if accumulation[intervalPre[m]] < min:
			min = accumulation[intervalPre[m]]
			minIndex = intervalPre[m]
	return minIndex

plt.figure()
plt.axis('off')
for plate, color in zip(plates, colors):
	gray_img = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
	# 若不分类会出现蓝牌白底黑字，其他黑底白字
	if color == 'blue':
		ret, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	else:
		ret, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
	# 去除车牌顶部的两棵钉
	rows, cols = thresh_img.shape[:2]
	for i in range(rows):
		jump, pixel = 0, thresh_img[i][0]
		for j in range(1, cols):
			if pixel != thresh_img[i][j]:
				jump += 1
				pixel = thresh_img[i][j]
		if jump < 8:
			thresh_img[i][:] = 0

	plt.imshow(thresh_img, cmap='gray')
	plt.show()

	# 分割字符
	hist_img = thresh_img.sum(axis=0)
	hist_max, hist_min = max(hist_img), min(hist_img)
	hist_img = (hist_img - hist_min) / (hist_max - hist_min)

	successive = []
	intervalPre = []
	isPreviousLess = 0
	for m in range(len(hist_img)):
		if isPreviousLess:
			if hist_img[m] <= 0.2:
				successive.append(m)
			else:
				isPreviousLess = 0
				intervalPre.append(successive)
				successive = []
		else:
			if hist_img[m] <= 0.2:
				isPreviousLess = 1
				successive.append(m)

	# 找到最大间隔，为省市和编号之间的间隔
	intervalLen = 0
	for n in range(len(intervalPre)):
		if len(intervalPre[n]) > intervalLen:
			intervalLen = len(intervalPre[n])
			bigInterval = intervalPre[n]
			bigIntervalIndex = n

	# 找到最大间隔的前一个间隔，即省简称和字母之间的间隔
	if bigIntervalIndex >= 1:
		minIndex = findInterval(hist_img, intervalPre[bigIntervalIndex - 1])

	thresh_img = thresh_img[:, minIndex:]  # 截取字母区域
	contours, heirachy = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 获取连通区域

	cntNum = 7 if color == 'green' else 6

	list = []
	for m in range(len(contours)):
		tuple = (m, cv2.contourArea(contours[m]))
		list.append(tuple)
	list.sort(key=lambda x: x[1], reverse=True)

	bigCnts = []  # 字母连通区域
	for n in range(cntNum):
		bigCnts.append(contours[list[n][0]])

	# 通过x坐标排序
	list = []
	for n in range(cntNum):  # 外接矩形
		x, y, width, height = cv2.boundingRect(bigCnts[n])
		tuple = (n, x)
		list.append(tuple)
	list.sort(key=lambda x: x[1])

	cnts = []  # 从左到右，字母连通区域
	for n in range(cntNum):
		cnts.append(bigCnts[list[n][0]])

	# 裁剪
	letters = []
	for cnt in cnts:
		x, y, width, height = cv2.boundingRect(cnt)
		letter = img[y:y + height, x:x + width]
		letter = cv2.resize(letter, (32, 64), interpolation=cv2.INTER_CUBIC)
		letters.append(letter)
	# imshow(str(cnt), letter)


	for letter in letters:
		plt.imshow(letter, cmap='gray')
		plt.show()


	# plate = cv2.cvtColor(plate, cv2.COLOR_BGR2RGB)
	# plt.subplot(1, 3, 1)
	# plt.imshow(plate)
	# plt.subplot(1, 3, 2)
	# plt.imshow(gray_img, cmap='gray')
	# plt.subplot(1, 3, 3)
	# plt.imshow(thresh_img, cmap='gray')
	# plt.show()































