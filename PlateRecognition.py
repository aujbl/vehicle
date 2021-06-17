import cv2
import numpy as np
import matplotlib.pyplot as plt

def imshow(img, name=''):
    cv2.imshow(name, img)
    cv2.waitKey(0)

def preprocess(img, b_size=(3, 3), kernel_size=(7, 20)):
    # 转灰度图 -> 高斯模糊 -> 二值化 -> 边缘检测 -> 形态学处理
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(img, b_size, 0)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    img = cv2.Canny(img, 100, 200)
    # imshow(img) # show canny result
    kernel = np.ones(kernel_size, np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    return img



if __name__ == '__main__':
    pic_file = './test_img/green.jpg'
    img = cv2.imread(pic_file)
    processed_img = preprocess(img)

    plt.subplot(1, 2, 1)
    plt.imshow(img)
    plt.subplot(1, 2, 2)
    plt.imshow(processed_img, cmap='gray')
    plt.show()







