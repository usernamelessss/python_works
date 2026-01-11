# -*- coding:utf-8 -*-
import os

import ddddocr
from PIL.Image import Image
from paddleocr import PaddleOCR
from paddleocr.tools.infer import predict_system


# from tools.infer import predict_system
# 用 ddddocr 识别图片文字,保存至 imgs_copy_word 文件夹
def ocrWords():
    ocr = ddddocr.DdddOcr(beta=False, show_ad=False)  # 识别
    word_map = {}
    for parent, dirnames, filenames in os.walk('imgs'):  # 遍历每一张图片
        for filename in filenames:
            k = filename.split('.')[0]
            currentPath = os.path.join(parent, filename)
            with open(currentPath, 'rb') as f:
                image = f.read()
            res = ocr.classification(image)
            if len(res) == 0:
                res = '未找到'
            if len(res) > 1:
                res = res[0]
            print(k, 'res:', res)
            os.makedirs('imgs_copy_word', exist_ok=True)
            d = f'{k}__{res}.jpg'
            img = Image.open(currentPath)
            img.save('imgs_copy_word/%s' % d)
            word_map[k] = res


if __name__ == '__main__':
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    image = r'F:\Home\Users\renjy\Desktop\Snipaste_2024-07-06_03-18-22.jpg'
    result = ocr.ocr(image, cls=True)
    print(result[0][0][-1][0])
    print("======================")
    print(result)

    # for line in result:
    #     print(line)
