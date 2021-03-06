# main.py - By: rick - 周五 10月 5 2018

import sensor, image, time, ustruct
from pyb import LED
from pyb import UART

## One time setup
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
clock = time.clock()
uart = UART(3, 115200, timeout_char=1000)



img = sensor.snapshot()
SIZE = (img.width(), img.height())
CENTER = (img.width() / 2, img.height() / 2)
AREA = img.size()

green_led = LED(1)
blue_led = LED(2)
#broken1_led  = LED(3)
#broken2_led    = LED(4)

appleRoi = ()

#apple_th = (30, 75, 50, 70 ,0, 40)
apple_th = (30, 75, 40, 70 , 20, 60)
#apple_th = (60, 90, 20, 60, -20, 10)

#maxRatio = 1.5
#minDensity = 0.4
#maxPixelCnt =
deltaXPixPerCycle = 2
deltaYPixPerCycle = 2


def borderCheck(Rect):
    Rect_0 = max(Rect[0], 0)
    Rect_1 = max(Rect[1], 0)
    maxW = min(Rect[2], SIZE[0] - Rect[0])
    maxH = min(Rect[3], SIZE[1] - Rect[1])
    return (Rect_0, Rect_1, maxW, maxH)

def extendRoi(Rect):
    v_x = Rect[0]
    v_y = Rect[1]
    r_width = Rect[2]
    r_height = Rect[3]

    xCenter = v_x + r_width / 2
    yCenter = v_y + r_height / 2

    r_width = r_width * 1.2
    r_height = r_height *1.2

    result = (int(xCenter - r_width/2), int(yCenter - r_height/2), int(r_width), int(r_height))

    return borderCheck(result)

def extendRoiWithBias(Rect, last_flag):
    v_x = Rect[0]
    v_y = Rect[1]
    r_width = Rect[2]
    r_height = Rect[3]

    xCenter = v_x + r_width / 2
    yCenter = v_y + r_height / 2

    const_x = 1
    const_y = 1

    # extend the area
    r_width = r_width * 1.2
    r_height = r_height *1.2

    # add the bias
    if last_flag[0] == 0:
        x_b = 0
    elif last_flag[0] == 1:
        x_b = -const_x # targe on right, roi turn left
    else:
        x_b = const_x

    if last_flag[1] == 0:
        y_b = 0
    elif last_flag[1] == 1:
        y_b = -const_y # target down, roi turn upwards
    else:
        y_b = const_y

    result = (int(xCenter - r_width/2 + x_b/2), int(yCenter - r_height/2 + y_b/2), int(r_width), int(r_height))
    return borderCheck(result)

def TargetIsCloseEnough(Rect):
    r_w = Rect[2]
    r_h = Rect[3]
    #area = r_w * r_h
    if ((r_w < 80 and r_h < 105)or(r_w < 105 and r_h < 80)):
    #if ((r_w < 60 and r_h < 85)or(r_w < 85 and r_h < 60)):
        return False
    return True

def judgeDirection(Blob):
    size = Blob.area()
    width = Blob.w()
    height = Blob.h()

    min_b_x = 10 * (1 + size/AREA)
    min_b_y = 10 * (1 + size/AREA)
    obj_center_x = Blob.cx()
    obj_center_y = Blob.cy()
    bias_x = obj_center_x - CENTER[0]
    bias_y = obj_center_y - CENTER[1]

    adj_cnt_x = int((bias_x - deltaXPixPerCycle) / deltaXPixPerCycle + 1)
    adj_cnt_y = int((bias_y - deltaYPixPerCycle) / deltaYPixPerCycle + 1)

    if abs(bias_x) < min_b_x:
        x_flag = 0 # still
    elif bias_x > 0:
        x_flag = 1 # target is on the right
    else:
        x_flag = 2 # target is on the left

    if abs(bias_y) < min_b_y:
        y_flag = 0 # still
    elif bias_y > 0:
        y_flag = 1 # target is down
    else:
        y_flag = 2 # target is up
    return [x_flag, y_flag], [adj_cnt_x, adj_cnt_y]


last_flag = [0, 0] # 0 for x, 1 for y
onDirAdjustXPeriod = 0
onDirAdjustYPeriod = 0
# flag for the direction adjustment status
onForwardPeriod = 0 # flag for the forwarding status

#uartClass:
#3,4 : 0
#1 : 1
#2 : 2
#7 : 3
#5,6 : 4


## Main program
while(True):

    clock.tick()
    print(clock.fps())
    green_led.off()
    blue_led.off()

    if onDirAdjustXPeriod > 0:
        # select the x dir flag
        uartClass = 0
        onDirAdjustXPeriod -= 1

    elif onDirAdjustYPeriod > 0:
        # select the y dir flag
        uartClass = 4
        onDirAdjustYPeriod -= 1
        if onDirAdjustYPeriod == 0:
            onForwardPeriod = 1
    else:
        if onForwardPeriod == 1:
            # select the forward flag
            uartClass = 1
            onForwardPeriod -= 1
        else:
            img = sensor.snapshot()
            img = img

        # find the blobs for apple
            # make sure the roi is not empty
            if appleRoi:
                # extend the roi, or the roi is likely to shrink on every loop
                appleRoiEx = extendRoiWithBias(appleRoi, last_flag)
                objBoxs = img.find_blobs([apple_th], pixels_threhold = 200, roi = appleRoiEx, merge = True, margin = 0)
                #print("roi found")
            else:
                objBoxs = img.find_blobs([apple_th], pixels_threhold = 200, merge = True, margin = 0)
                #print("roi not founded!")

            if objBoxs:
                maxArea = 0
                mIndex = 0
                for i in range(0, len(objBoxs)):
                    img.draw_rectangle(objBoxs[i].rect())
                    if objBoxs[i].area() > maxArea:
                        maxArea = objBoxs[i].area()
                        mIndex = i
                objBlob = objBoxs[mIndex]
                appleRoi = objBlob.rect()
                img.draw_rectangle(appleRoi, color = (255, 255, 0))
                print("obj found")

                #[last_flag, last_adj_cnt] = judgeDirection(objBlob)
                last_flag, last_adj_cnt = judgeDirection(objBlob)
                #last_adj_cnt = last[1]
                print("1")
                print(last_flag)
                print('\n')
                #last_flag = last[0]
                print("2")
                print(last_adj_cnt)
                onDirAdjustXPeriod = last_adj_cnt[0]
                onDirAdjustYPeriod = last_adj_cnt[1]
                # select the x flag
                uartClass = 0
                onDirAdjustXPeriod -= 1

                # when the target is close enough, shift into auto mode
                if TargetIsCloseEnough(appleRoi):
                    #select the cut flag
                    uartClass = 3


                green_led.on()



            else:
                # lost the frame: extend the area, and backward
                appleRoi = []
                #if appleRoi:
                    #appleRoi = extendRoi(appleRoi)
                    #img.draw_rectangle(appleRoi, color = (0, 0, 255))
                # select the backwards flag
                uartClass = 2
                print("obj not found!")

                blue_led.toggle()
                #continue

            #print('\n')

        # get the info of density and ratio of target
            #density = objBlob.density()
            #ratio = objBlob.w() / objBlob.h()
            #pixelCnt = objBlob.pixels()
            #area = objBlob.area()
            #img.draw_string(appleRoi[0], appleRoi[1], str(density), color = (255, 255, 0))
            #print("pix: %d,  area: %d, width: %d, height: %d"%(pixelCnt, area, objBlob.w(), objBlob.h()))



    # send the flag

#uartFlag:
#0x00: stop; 0x01: forward; 0x02: back; 0x03: turnL;
#0x04: turnR; 0x05: HeadUP; 0x06: HeadDOWN; 0x07: CUT;

    # left or right
    if uartClass == 0:
        if last_flag[0] == 0:
            uart.write(ustruct.pack("b", 0x00))
            print("%s sent" %("stop"))
        if last_flag[0] == 1:
            uart.write(ustruct.pack("b", 0x04))
            print("%s sent" %("right"))
        else:
            uart.write(ustruct.pack("b", 0x03))
            print("%s sent" %("left"))

    # forward
    if uartClass == 1:
        uart.write(ustruct.pack("b", 0x01))
        print("%s sent" %("forward"))

    # stop
    if uartClass == 2:
        uart.write(ustruct.pack("b", 0x00))
        print("%s sent" %("stop"))

    # cut
    if uartClass == 3:
        uart.write(ustruct.pack("b", 0x07))
        print("%s sent" %("cut"))

    # up or down
    if uartClass == 4:
        if last_flag[1] == 0:
            uart.write(ustruct.pack("b", 0x00))
            print("%s sent" %("stop"))
        if last_flag[1] == 1:
            uart.write(ustruct.pack("b", 0x06))
            print("%s sent" %("down"))
        else:
            uart.write(ustruct.pack("b", 0x05))
            print("%s sent" %("up"))

    #time.sleep(30)
    print('\n')
