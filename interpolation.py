#coding:utf-8
from numpy import *
import arcpy
import func



###

# 改进了之前的插值曲线算法。
#
# 通过旋转，先转到坐标水平的位置，再插值，插值完再转回来。
#
# 另外，调头的曲线，单独判断完再插值.
###
def pre_rotate(pt1, l1, pt2, l2):
    if pt1.X == pt2.X:
        pt1.X -= 0.0001
    ang = func.get_angle(pt1, pt2)
    ang = arctan(ang)
    pt_mid = arcpy.Point((pt1.X+pt2.X)/2,(pt1.Y+pt2.Y)/2)
    pt11 = func.rotate_pt(pt1, pt_mid, ang)
    pt21 = func.rotate_pt(pt2, pt_mid, ang)
    if func.likelyequal(l1, l2):
        l11 = 0
        l21 = 0
    else:
        l11 = tan(arctan(l1)-ang)
        l21 = tan(arctan(l2)-ang)
    [pt_list, count_flag] = polation(pt11, l11, pt21, l21)
    pt_list2 = []
    for pt in pt_list:
        pt = func.rotate_pt(pt, pt_mid, -ang)
        pt_list2.append(pt)
    return [pt_list2, count_flag]


def polation(pt2, l1, pt3, l2):
    x0 = pt2.X; y0 = pt2.Y; x00 = pt3.X; y00 = pt3.Y
    step = abs((x00 - x0)/10)
    pt2.X -= x0; pt2.Y -= y0; pt3.X -= x0; pt3.Y -= y0
    m1 = mat([[3*pt2.X**2, 2*pt2.X, 1, 0.0000001],
             [3*pt3.X**2, 2*pt3.X, 1, 0.0000001],
             [pt2.X**3, pt2.X**2, pt2.X, 1],
             [pt3.X**3, pt3.X**2, pt3.X, 1]])
    m2 = mat([[l1],
             [l2],
             [pt2.Y],
             [pt3.Y]])
    res_m = m1.I*m2
    a = res_m.tolist()[0][0]
    b = res_m.tolist()[1][0]
    c = res_m.tolist()[2][0]
    d = res_m.tolist()[3][0]
    pt_list = []
    x = min(pt2.X, pt3.X)
    # x += 0.01*0.001
    x2 = max(pt2.X, pt3.X)
    count_flag = 0
    while x < x2:
        y = a*x**3 + b*x**2 + c*x + d
        pt_list.append(arcpy.Point(x, y))
        x += step
        count_flag += 1
        print [count_flag, x, x2]
    # test
    x = x2
    y = a * x ** 3 + b * x ** 2 + c * x + d
    pt_list.append(arcpy.Point(x, y))
    for pt in pt_list:
        pt.X += x0
        pt.Y += y0
    pt2.X += x0; pt2.Y += y0; pt3.X += x0; pt3.Y += y0
    return [pt_list, count_flag]

def test():
    pt1 = arcpy.Point(116.43656223,21.2340178663)
    pt2 = arcpy.Point(116.436525185,21.2338593148)
    res = polation(pt1, -0.940425531916, pt2, 0.679563711134)
    print res

