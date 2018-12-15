# implementation of SLIC Superpixel algorithm
# reference: SLIC Superpixels Compared to State-of-the-art Superpixel Methods
# DOI: 10.1109/TPAMI.2012.120
# website: https://infoscience.epfl.ch/record/177415
# reference: SLIC算法分割超像素原理及Python实现: https://www.kawabangga.com/posts/1923
import cv2 as cv
import numpy as np
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--image', default="Lena.jpg", type=str, help='input image name')
parser.add_argument('--k', default=1000, type=int, help='number of clusters')
parser.add_argument('--m', default=30, type=int, help='balancing parameter')
args = parser.parse_args()


class Block(object):
    def __init__(self, num, h, w, l=0, a=0, b=0):
        self.number = num
        self.h = h
        self.w = w
        self.l = l
        self.a = a
        self.b = b
        self.pixels = []  # positions of the pixels which belongs to this block

    def change_pos(self, h, w):
        self.h = h
        self.w = w

    def change_color(self, l, a, b):
        self.l = l
        self.a = a
        self.b = b


class Cluster(object):
    def __init__(self, image, number, m):
        self.image = image
        self.k = number
        self.m = m
        self.height = image.shape[0]
        self.width = image.shape[1]
        self.pixels = self.height * self.width
        self.block_length = int(np.sqrt(self.pixels / self.k))

        self.label = np.full((self.height, self.width), -1, np.int32)
        self.dis = np.full_like(self.label, np.inf, np.float32)
        self.blocks = []
        self.grad = cv.Laplacian(self.image, cv.CV_64F)

        w = 0
        h = self.block_length
        j = 0
        # in case that only half of the last line is covered
        for i in range(self.k + 2 * int(self.width / self.block_length)):
            w += self.block_length
            if (i % 2) == 0:
                h -= int((self.block_length - 1) / 2)
                if h < 0:
                    break
            else:
                h += int((self.block_length - 1) / 2)
                if h >= self.height:
                    break
            if w >= self.width:
                if (j % 2) == 0:
                    w = self.block_length
                else:
                    w = int(self.block_length / 2)
                h += self.block_length
                j += 1
                if h >= self.height:
                    break
            self.blocks.append(Block(i, h, w))

        self.adjust_blocks()

    # adjust the positions of block centers
    # move them to the points with the minimum gradients within the 3x3 regions
    def adjust_blocks(self):
        for block in self.blocks:
            min_grad = np.sum(self.grad[block.h][block.w])
            min_h = block.h
            min_w = block.w
            for i in range(-1, 2):
                if block.h + i < 0 or block.h + i >= self.height:
                    continue  # in case that the index goes out of boundary
                for j in range(-1, 2):
                    if block.w + j < 0 or block.w + j >= self.width:
                        continue
                    new_grad = np.sum(self.grad[block.h + i][block.w + j])
                    if new_grad < min_grad:
                        min_grad = new_grad
                        min_h = block.h + i
                        min_w = block.w + j
            block.change_pos(min_h, min_w)
            block.pixels.append((min_h, min_w))

    def distance(self, h1, w1, h2, w2):
        l1 = int(self.image[h1][w1][0])
        l2 = int(self.image[h2][w2][0])
        a1 = int(self.image[h1][w1][1])
        a2 = int(self.image[h2][w2][1])
        b1 = int(self.image[h1][w1][2])
        b2 = int(self.image[h2][w2][2])
        d_lab = np.sqrt((np.square(l1 - l2) + np.square(a1 - a2) + np.square(b1 - b2)))
        d_xy = np.sqrt(np.square(h1 - h2) + np.square(w1 - w2))
        distance = d_lab + d_xy * (self.m / self.block_length)
        return distance

    def assign(self):
        for block in self.blocks:
            for h2 in range(block.h - 2 * self.block_length, block.h + 2 * self.block_length):
                # out of boundary
                if h2 < 0:
                    continue
                if h2 >= self.height:
                    break

                # in boundary
                for w2 in range(block.w - 2 * self.block_length, block.w + 2 * self.block_length):
                    # out of boundary
                    if w2 < 0:
                        continue
                    if w2 >= self.width:
                        break

                    # in boundary
                    d = self.distance(block.h, block.w, h2, w2)
                    if self.label[h2][w2] < 0 or d < self.dis[h2][w2]:
                        if self.label[h2][w2] >= 0:
                            self.blocks[int(self.label[h2][w2])].pixels.remove((h2, w2))
                        self.label[h2][w2] = block.number
                        self.dis[h2][w2] = d
                        block.pixels.append((h2, w2))

            # re-compute the center of the block
            number_pixels = len(block.pixels)
            new_h = 0
            new_w = 0
            for pixel in block.pixels:
                new_h += pixel[0]
                new_w += pixel[1]

            new_h = int(new_h / number_pixels)
            new_w = int(new_w / number_pixels)
            block.change_pos(new_h, new_w)
            block.pixels.append((new_h, new_w))

    def color(self):
        for block in self.blocks:
            avg_l = 0
            avg_a = 0
            avg_b = 0
            length = len(block.pixels)
            for pixel in block.pixels:
                _l = int(self.image[pixel[0]][pixel[1]][0])
                _a = int(self.image[pixel[0]][pixel[1]][1])
                _b = int(self.image[pixel[0]][pixel[1]][2])
                avg_l += _l
                avg_a += _a
                avg_b += _b
            avg_l = int(avg_l / length)
            avg_a = int(avg_a / length)
            avg_b = int(avg_b / length)
            block.change_color(avg_l, avg_a, avg_b)  # use the average color

    def output(self):
        new_image = np.zeros_like(self.image)
        self.color()
        for block in self.blocks:
            for pixel in block.pixels:
                new_image[pixel[0]][pixel[1]][0] = block.l
                new_image[pixel[0]][pixel[1]][1] = block.a
                new_image[pixel[0]][pixel[1]][2] = block.b
            '''
            new_image[block.h][block.w][0] = 0
            new_image[block.h][block.w][1] = 0
            new_image[block.h][block.w][2] = 0
            '''
        new_image = cv.cvtColor(new_image, cv.COLOR_LAB2BGR)
        return new_image


if __name__ == '__main__':
    file_name = args.image
    cluster_number = args.k
    m_param = args.m

    img = cv.imread(file_name)
    img = cv.cvtColor(img, cv.COLOR_BGR2LAB)
    app = Cluster(image=img, number=int(cluster_number), m=int(m_param))
    for it in range(10):
        app.assign()
        out_image = app.output()
        name = "_new_" + str(it) + ".jpg"
        cv.imwrite(name, out_image)
        print(it)
