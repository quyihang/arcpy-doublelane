#coding:utf-8
import arcpy
import func
import interpolation
import json

LANE_WIDTH = 5

class doubleLineConvert():
    def __init__(self, lineLayer, nodeLayer, outputLineLayer, outputNodeLayer):
        self.lineLayer = lineLayer
        self.nodeLayer = nodeLayer
        self.outputLineLayer = outputLineLayer
        self.outputNodeLayer = outputNodeLayer
        self.nodeList = []
        self.outputNodeList = [] # 这名字写大不太对。它其实是用来存，来算之后的output_node_id。 结构{'id':1.'num':1}
        self.trueOutputNodeList = []
        self.lineList = []

    def readData(self):
        if arcpy.Describe(self.lineLayer).shapetype <> u'Polyline' or arcpy.Describe(self.nodeLayer).shapetype <> u'Point':
            return
        self.readNode(self.nodeLayer)

    def readNode(self, nodeLayer):
        for row in arcpy.da.SearchCursor(nodeLayer,("Id","SHAPE@XY")):
            id = row[0]
            lng = row[1][0]
            lat = row[1][1]
            self.nodeList.append([id,lng,lat])
            self.outputNodeList.append({'id':id, 'num':0})

    def dealLine(self):
        for row in arcpy.da.SearchCursor(self.lineLayer,("FID","Forward_L","Backward_L","Start_Node","End_Node","SHAPE@")):
            self.lineList.append(row)
        for row in self.lineList:
            id = row[0]; forward_lane = row[1]; backward_lane = row[2]; start_node = row[3]; end_node = row[4]; pts = row[-1]
            # self.lineList.append(row)
            pt_array = []
            for part in pts:
                # 这里我就把part分开成不同记录的数了。然后之后根据line的index和node关联起来
                for pt in part:
                    pt_array.append(pt)
            [intend_head, intend_tail] = self.get_intend(row)
            if forward_lane != 0 and backward_lane != 0:
                self.shift_lane_double(pt_array, start_node, end_node, forward_lane, backward_lane, intend_head, intend_tail) # 好像是后面这个。得到证实了。
            else:
                if forward_lane != 0:
                    self.no_shift_lane(pt_array, start_node, end_node, forward_lane, intend_head, intend_tail)
                elif backward_lane != 0:
                    self.no_shift_lane(pt_array, end_node, start_node, backward_lane, intend_head, intend_tail)
            # self.shift_lane(start_node,end_node,forward_lane)
            # self.shift_lane(end_node,start_node,backward_lane)

    '''
    def shift_lane(self, start, end, lane): # node_list, lane, intend_head, intend_tail
        cursor = arcpy.da.InsertCursor(self.outputLineLayer,("lane_count","SHAPE@"))
        # cursor = arcpy.da.InsertCursor(self.outputLineLayer,("lane_count","SHAPE@"))
        start_pt = []; end_pt = []
        for row in self.nodeList:
            if start == row[0]:
                start_pt = [row[1],row[2]]
            if end == row[0]:
                end_pt = [row[1],row[2]]
        arcpy.AddMessage(str([start, end, self.nodeList]))
        dx = end_pt[0] - start_pt[0]; dy = end_pt[1] - start_pt[1]
        l = [num / ((dy ** 2 + dx ** 2) ** 0.5) for num in [-dy, dx]]
        start_pt_l = [start_pt[0]+l[0]*lane*0.01*0.001*LANE_WIDTH, start_pt[1]+l[1]*lane*0.01*0.001*LANE_WIDTH]
        end_pt_l = [end_pt[0]+l[0]*lane*0.01*0.001*LANE_WIDTH, end_pt[1]+l[1]*lane*0.01*0.001*LANE_WIDTH]
        array = arcpy.Array([arcpy.Point(start_pt_l[0],start_pt_l[1]),
                             arcpy.Point(end_pt_l[0],end_pt_l[1])])
        arcpy.AddMessage(str(array))
        polyline = arcpy.Polyline(array)
        # cursor.insertRow((lane,polyline))
        cursor.insertRow((lane,polyline))
        del cursor
    '''

    def get_intend(self, line):
        start_node = line[3]; end_nod = line[4]; pts = line[-1]
        nearby_lines = []
        for row in self.lineList:
            forward_lane_row = row[1]; backward_lane_row = row[2]; start_node_row = row[3]; end_node_row = row[4]; pts_row = row[-1]
            if start_node == start_node_row or start_node == end_node_row:
                nearby_lines.append(row)
        intend_head = self.get_intend_head(line, nearby_lines)
        nearby_lines = []
        for row in self.lineList:
            forward_lane_row = row[1]; backward_lane_row = row[2]; start_node_row = row[3]; end_node_row = row[4]; pts_row = row[-1]
            if end_nod == start_node_row or end_nod == end_node_row:
                nearby_lines.append(row)
        intend_tail = self.get_intend_tail(line, nearby_lines)
        return [intend_head, intend_tail]

    def get_intend_head(self, line, nearby_lines):
        intend = 4*LANE_WIDTH
        if len(nearby_lines) == 0:
            intend = 0
        else:
            lane_list = []
            for n_line in nearby_lines:
                lane_list.append(n_line[1])
                lane_list.append(n_line[2])
            intend = max(lane_list)*LANE_WIDTH
        return intend

    def get_intend_tail(self, line, nearby_lines):
        intend = 4*LANE_WIDTH
        if len(nearby_lines) == 0:
            intend = 0
        else:
            lane_list = []
            for n_line in nearby_lines:
                lane_list.append(n_line[1])
                lane_list.append(n_line[2])
            intend = max(lane_list)*LANE_WIDTH
        return intend

    # 代码不支持多段part，请提前分离好！
    def shift_lane_double(self, pt_array, start_node_id, end_node_id, lane_forward, lane_backward, intend_head, intend_tail):
        line_cursor = arcpy.da.InsertCursor(self.outputLineLayer, ("from_id", "to_id", "lane_count", "SHAPE@"))
        node_cursor = arcpy.da.InsertCursor(self.outputNodeLayer, ("parent_nod", "from_to", "node_id", "SHAPE@", "angle")) # from/start: 0   to/end: 1
        direct_flag = True # 用来判断起点id和node_array存储起点是否一致。一致为True，不一致为False
        for row in self.nodeList:
            if start_node_id == row[0]: # 然后再判断，这个start_node到底是头上的还是尾巴上的
                if func.compare(row[1],row[2],pt_array[0]):
                    pt_array = func.cut_head(pt_array, intend_head)
                elif func.compare(row[1],row[2],pt_array[-1]):
                    direct_flag = False
                    pt_array = func.cut_tail(pt_array, intend_head)
            if end_node_id == row[0]:
                if func.compare(row[1],row[2],pt_array[0]):
                    direct_flag = False
                    pt_array = func.cut_head(pt_array, intend_tail)
                elif func.compare(row[1],row[2],pt_array[-1]):
                    pt_array = func.cut_tail(pt_array,intend_tail)
        [vec_r, vec_l] = func.shift_vector(pt_array, lane_forward*LANE_WIDTH, lane_backward*LANE_WIDTH, direct_flag)
        [pt_array_r, node_start_r, angle_start_r, node_end_r, angle_end_r] = func.move_pts_right(pt_array, vec_r)
        [pt_array_l, node_start_l, angle_start_l, node_end_l, angle_end_l] = func.move_pts_left(pt_array, vec_l)
        # 设计一个node_id的方法 # 插入了四个点
        if direct_flag == True:
            node_id_f = self.get_output_node_id(start_node_id)
            node_cursor.insertRow((start_node_id, 0, node_id_f, node_start_r, angle_start_r)) # todo # 这里严查入两根线。起点终点id又要搞一搞了
            self.trueOutputNodeList.append({"node_id": node_id_f, "parent_nod": start_node_id, "from_to": 0, "SHAPE": node_start_r, "angle": angle_start_r})
            node_id_t = self.get_output_node_id(end_node_id)
            node_cursor.insertRow((end_node_id, 1, node_id_t, node_end_r, angle_end_r))
            self.trueOutputNodeList.append({"node_id": node_id_t, "parent_nod": end_node_id, "from_to": 1, "SHAPE": node_end_r, "angle": angle_end_r})
            line = arcpy.Polyline(arcpy.Array(pt_array_r))
            line = func.judgeDirect(node_start_r, line)
            line_cursor.insertRow((node_id_f, node_id_t, lane_forward, line))
            node_id_f = self.get_output_node_id(end_node_id)
            node_cursor.insertRow((end_node_id, 0, node_id_f, node_start_l, angle_start_l))
            self.trueOutputNodeList.append({"node_id": node_id_f, "parent_nod": end_node_id, "from_to": 0, "SHAPE": node_start_l, "angle": angle_start_l})
            node_id_t = self.get_output_node_id(start_node_id)
            node_cursor.insertRow((start_node_id, 1, node_id_t, node_end_l, angle_end_l))
            self.trueOutputNodeList.append({"node_id": node_id_t, "parent_nod": start_node_id, "from_to": 1, "SHAPE": node_end_l, "angle": angle_end_l})
            line = arcpy.Polyline(arcpy.Array(pt_array_l))
            line = func.judgeDirect(node_start_l, line)
            line_cursor.insertRow((node_id_f, node_id_t, lane_backward, line))
        elif direct_flag == False:
            node_id_f = self.get_output_node_id(end_node_id)
            node_cursor.insertRow((end_node_id, 0, node_id_f, node_start_r, angle_start_r))
            self.trueOutputNodeList.append({"node_id": node_id_f, "parent_nod": end_node_id, "from_to": 0, "SHAPE": node_start_r, "angle": angle_start_r})
            node_id_t = self.get_output_node_id(start_node_id)
            node_cursor.insertRow((start_node_id, 1, node_id_t, node_end_r, angle_end_r))
            self.trueOutputNodeList.append({"node_id": node_id_t, "parent_nod": start_node_id, "from_to": 1, "SHAPE": node_end_r, "angle": angle_end_r})
            line = arcpy.Polyline(arcpy.Array(pt_array_r))
            line = func.judgeDirect(node_start_r, line)
            line_cursor.insertRow((node_id_f, node_id_t, lane_backward, line))
            node_id_f = self.get_output_node_id(start_node_id)
            node_cursor.insertRow((start_node_id, 0, node_id_f, node_start_l, angle_start_l))
            self.trueOutputNodeList.append({"node_id": node_id_f, "parent_nod": start_node_id, "from_to": 0, "SHAPE": node_start_l, "angle": angle_start_l})
            node_id_t = self.get_output_node_id(end_node_id)
            node_cursor.insertRow((end_node_id, 1, node_id_t, node_end_l, angle_end_l))
            self.trueOutputNodeList.append({"node_id": node_id_t, "parent_nod": end_node_id, "from_to": 1, "SHAPE": node_end_l, "angle": angle_end_l})
            line = arcpy.Polyline(arcpy.Array(pt_array_l))
            line = func.judgeDirect(node_start_l, line)
            line_cursor.insertRow((node_id_f, node_id_t, lane_forward, line))


    def no_shift_lane(self, pt_array, start_node_id, end_node_id, lane, intend_head, intend_tail):  # 这里逻辑稍微改变一下。先调准顺序
        line_cursor = arcpy.da.InsertCursor(self.outputLineLayer, ("from_id", "to_id", "lane_count", "SHAPE@"))
        node_cursor = arcpy.da.InsertCursor(self.outputNodeLayer, ("parent_nod", "from_to", "node_id", "SHAPE@", "angle")) # from/start: 0   to/end: 1
        direct_flag = True # 用来判断起点id和node_array存储起点是否一致。一致为True，不一致为False
        for row in self.nodeList:
            if start_node_id == row[0]:
                start_node = arcpy.Point(row[1], row[2])
            if end_node_id == row[0]:
                end_node = arcpy.Point(row[1], row[2])
        if not (func.compare_pt(start_node, pt_array[0])):
            pt_array = list(reversed(pt_array))
        pt_array = func.cut_head(pt_array, intend_head)
        pt_array = func.cut_tail(pt_array, intend_tail)
        node_id_f = self.get_output_node_id(start_node_id)
        node_id_t = self.get_output_node_id(end_node_id)
        line = arcpy.Polyline(arcpy.Array(pt_array))
        line_cursor.insertRow((node_id_f, node_id_t, lane, line))
        node_f = pt_array[0]; node_t = pt_array[-1]
        angle_f = func.get_angle(pt_array[0], pt_array[1])
        angle_t = func.get_angle(pt_array[-1], pt_array[-2])
        node_cursor.insertRow((start_node_id, 0, node_id_f, node_f, angle_f))
        self.trueOutputNodeList.append({"node_id": node_id_f, "parent_nod": start_node_id, "from_to": 0, "SHAPE": node_f, "angle": angle_f})
        node_cursor.insertRow((end_node_id, 1, node_id_t, node_t, angle_t))
        self.trueOutputNodeList.append({"node_id": node_id_t, "parent_nod": end_node_id, "from_to": 1, "SHAPE": node_t, "angle": angle_t})
        return

    def get_output_node_id(self, origin_node_id):  # todo # 我对我写出来的算法还知之甚少啊。。
        output_node_id = origin_node_id
        for outputNode in self.outputNodeList:
            if outputNode['id'] == origin_node_id:
                outputNode['num'] += 1
                tail_num_str = str(outputNode['num'])
                if len(tail_num_str) <= 1:
                    tail_num_str = '0'+str(outputNode['num'])
                output_node_id = int(str(origin_node_id)+tail_num_str)
                break
        return output_node_id

    def curve_inter(self):
        draw_line = 0
        curve_cursor = arcpy.da.InsertCursor(self.outputLineLayer, ("from_id", "to_id", "lane_count", "SHAPE@", "node_count"))
        for oNode in self.trueOutputNodeList:
            if oNode['from_to'] == 1:
                for osNode in self.trueOutputNodeList:
                    if (oNode['parent_nod'] == osNode['parent_nod']) and (osNode['from_to'] == 0): # 这里表示从一个标记为1的终点，连线上标记为0的起点 # oNode起osNode终
                        draw_line += 1
                        print 'line_count: '+str(draw_line)
                        [pt_list, count_flag] = interpolation.pre_rotate(oNode['SHAPE'], oNode['angle'], osNode['SHAPE'], osNode['angle'])
                        print 'list_pt_count: '+str(len(pt_list))
                        line = arcpy.Polyline(arcpy.Array(pt_list))
                        print line
                        print line.length
                        line = func.judgeDirect(oNode['SHAPE'], line)
                        curve_cursor.insertRow((oNode['node_id'], osNode['node_id'], 2, line, count_flag))


if __name__ == '__main__':
    # lineLayer = arcpy.GetParameterAsText(0)
    # nodeLayer = arcpy.GetParameterAsText(1)
    # outputLineLayer = arcpy.GetParameterAsText(2)
    # outputNodeLayer = arcpy.GetParameterAsText(3)
    lineLayer = 'C:/Users/qu/Desktop/bishe/data/test/convert_beijing/road_test.shp'
    nodeLayer = 'C:/Users/qu/Desktop/bishe/data/test/convert_beijing/nodes_test.shp'
    outputLineLayer = 'C:/Users/qu/Desktop/bishe/data/test/convert_beijing/output_road.shp'
    outputNodeLayer = 'C:/Users/qu/Desktop/bishe/data/test/convert_beijing/output_node.shp'
    # arcpy.AddMessage(lineLayer)
    # arcpy.AddMessage(nodeLayer)
    # arcpy.AddMessage(outputLineLayer)
    # arcpy.AddMessage(outputNodeLayer)
    iDoubleLine = doubleLineConvert(lineLayer,nodeLayer,outputLineLayer,outputNodeLayer)
    iDoubleLine.readData()
    iDoubleLine.dealLine()
    iDoubleLine.curve_inter()