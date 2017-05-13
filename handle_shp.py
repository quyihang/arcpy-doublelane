#coding:utf8
import arcpy
import func

# 策略：读点，存好。读线，存好。然后看点在哪两条线的交界。如果不在两个线（只接触一根线），那就先留着，原来的0值，之后再去算它。

def readline(strpath):
    line_list = []
    total_list = []
    for row in arcpy.da.SearchCursor(strpath, ("SHAPE@", 'FNO', 'TNO')):
        line_list.append(row)
    for line in line_list:
        pt_list = []
        record = []
        for part in line[0]:
            for pt in part:
                pt_list.append(pt)
        record.append(pt_list[0])
        record.append(pt_list[-1])
        record.append(line[1])
        record.append(line[2])
        record.append(0)
        total_list.append(record)
    return total_list

def get_list_max(list):
    for item in list:
        if list.count(item) > 1:
            return item
    return -1


if __name__ == '__main__':
    lineLayer = 'C:/Users/qu/Desktop/bishe/data/now/RoadLink.shp'
    nodeLayer = 'C:/Users/qu/Desktop/bishe/data/now/RoadLink_ND_Junctions.shp'
    total_list = readline(lineLayer)
    print "reading lines ..."
    rows = arcpy.da.UpdateCursor(nodeLayer, ("SHAPE@", "join_id"))
    for row in rows:
        if row[1] != 0:
            continue
        no_list = []
        pt1 = row[0]
        for line in total_list:
            if line[4] > 1:
                continue
            ptlist = []
            if func.compare_pt(pt1.labelPoint, line[0]) or func.compare_pt(pt1.labelPoint, line[1]):
                print "!!!"
                no_list.append(line[2])
                no_list.append(line[3])
                if len(no_list) > 2:
                    line[4] += 1
                    break
        row[1] = get_list_max(no_list)
        print row[1]
        rows.updateRow(row)
        print "update!"