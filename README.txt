Apple detector思路：
１.筛选苹果目标的方式非常的暴力，就是用的LAB颜色阈值，由于摄像头的底片处于量子状态，所以准备了两套参数,openmv有个函数find_blobs可以集成了颜色挑选和轮廓查找。
2.合并临近blob的用意：排除小区域的干扰／其次，我们接受多个水果重合的情况。
3.挑选最大面积的blob：最大面积的blob一定是苹果／很有可能是多个苹果的重合
4.跟踪机制：找到最大的区域就保持跟踪这个区域，直接进行暴力roi跟踪。
但是考虑到如果在原尺寸roi上继续寻找，由于颜色阈值化结果的不稳定性，极有可能导致roi不断缩小的情况，这一点已被实际情况证实。所以我们每次需要扩展roi，这样能够保持稳定。
5.增加远近情况的区分：远时box不准确影响不大，但是一旦到达一定的距离会对苹果的大小评估失真。
6.
