#coding:utf-8
import arcpy
from numpy import *

def vector(pt1, pt2): # 从pt1到pt2的单位向量
    length = ((pt1.X-pt2.X)**2+(pt1.Y-pt2.Y)**2)**0.5
    return [(pt2.X - pt1.X)/length, (pt2.Y - pt1.Y)/length]


def cut_head(pt_arr, cut_len):
    pt1 = pt_arr[0]
    pt2 = pt_arr[1]
    vec = vector(pt1, pt2)
    pt1_1 = arcpy.Point(pt1.X + vec[0] * cut_len, pt1.Y + vec[1] * cut_len)
    pt_arr_2 = [pt1_1] + pt_arr[1:]
    return pt_arr_2


def cut_tail(pt_arr, cut_len):
    pt1 = pt_arr[-1]
    pt2 = pt_arr[-2]
    vec = vector(pt1, pt2)
    pt1_1 = arcpy.Point(pt1.X + vec[0] * cut_len, pt1.Y + vec[1] * cut_len)
    pt_arr_2 = pt_arr[:-1] + [pt1_1]
    return pt_arr_2


def compare(x, y, pt):
    flag = False
    if ((abs(pt.X-x))**2 + (abs(pt.Y-y))**2) < 0.000000001:
        flag = True
    else:
        flag = False
    return flag

def compare_pt(pt1, pt2):
    if ((abs(pt1.X-pt2.X))**2 + (abs(pt1.Y-pt2.Y))**2) < 0.000000001:
        flag = True
    else:
        flag = False
    return flag

def likelyequal(a,b):
    if abs(a-b)<0.000001:
        return True
    else:
        return False


def shift_vector(pt_array, width_forward, width_backward, direct_flag): # 方向是起点到终点的方向之垂直，正向为左，逆向为右。方向flag为True，则起点就是pt_array的起点，False则起点是pt_array的终点
    start_pt = pt_array[0]
    end_pt = pt_array[-1]
    # if direct_flag == True:
    #     pass
    # elif direct_flag == False:
    #     start_pt = pt_array[-1]
    #     end_pt = pt_array[0]
    vec = vector(start_pt, end_pt)
    if direct_flag:
        vec_r = [vec[1]*width_forward/2, -vec[0]*width_forward/2]
        vec_l = [-vec[1]*width_backward/2, vec[0]*width_backward/2]
    else:
        vec_r = [vec[1]*width_backward/2, -vec[0]*width_backward/2]
        vec_l = [-vec[1]*width_forward/2, vec[0]*width_forward/2]
    return [vec_r, vec_l]

def move_pts_right(pt_array, vec): # 这里最好把始末node也加进去
    pt_array_res = []
    for pt in pt_array:
        pt_res = move_pt(pt, vec)
        pt_array_res.append(pt_res)
    node_start = move_pt(pt_array[0], vec)
    angle_start = get_angle(pt_array[0], pt_array[1])
    node_end = move_pt(pt_array[-1], vec)
    angle_end = get_angle(pt_array[-1], pt_array[-2])
    return [pt_array_res, node_start, angle_start, node_end, angle_end]

def move_pts_left(pt_array, vec):
    pt_array_res = []
    for pt in pt_array:
        pt_res = move_pt(pt, vec)
        pt_array_res.append(pt_res)
    node_start = move_pt(pt_array[-1], vec)
    angle_start = get_angle(pt_array[-1], pt_array[-2])
    node_end = move_pt(pt_array[0], vec)
    angle_end = get_angle(pt_array[0], pt_array[1])
    return [pt_array_res, node_start, angle_start, node_end, angle_end]

def move_pt(pt, vec):
    pt_res = arcpy.Point(pt.X+vec[0], pt.Y+vec[1])
    return pt_res

def get_angle(pt1, pt2):  # 这里的angle其实是tan
    if abs(pt2.X-pt1.X) < 0.000001:
        return 999999.0
    else:
        return (pt1.Y - pt2.Y) / (pt1.X - pt2.X)

def judgeDirect(node_start, line):
    if node_start == '':
        print 1
    for part in line:
        for pt in part:
            if pt.X == node_start.X and pt.Y == node_start.Y:
                return line
            else:
                line = reverseLine(line)
                return line
    return

def reverseLine(line):
    line_l = []
    for part in line:
        for pt in part:
            line_l.append(pt)
    line_reverse = list(reversed(line_l))
    line = arcpy.Polyline(arcpy.Array(line_reverse))
    return line

def dist_pt(pt1, pt2):
    dist = ((pt1.X-pt2.X)**2+(pt1.Y-pt2.Y)**2)**0.5
    return dist

def rotate_vec(vec, ang):
    vec1 = mat([vec])
    angmat = mat([[cos(ang),-sin(ang)],
                  [sin(ang),cos(ang)]])
    vec2 = vec1*angmat
    return [vec2.tolist()[0][0], vec2.tolist()[0][1]]


def rotate_pt(pt1, pt_mid, ang):
    vec = [pt1.X - pt_mid.X, pt1.Y - pt_mid.Y]
    vec2 = rotate_vec(vec, ang)
    x = pt_mid.X + vec2[0]
    y = pt_mid.Y + vec2[1]
    return arcpy.Point(x, y)