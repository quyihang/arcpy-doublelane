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

def the_other(num1, num2, num_list):
    if num1 in num_list:
        return num2
    return num1


def main1():
    lineLayer = 'C:/Users/qu/Desktop/bishe/data/part/part.shp'
    nodeLayer = 'C:/Users/qu/Desktop/bishe/data/part/part_junctions.shp'
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

def main2():
    lineLayer = 'C:/Users/qu/Desktop/bishe/data/part/part.shp'
    nodeLayer = 'C:/Users/qu/Desktop/bishe/data/part/part_junctions.shp'
    total_list = readline(lineLayer)
    print "reading lines ..."
    rows = arcpy.da.SearchCursor(nodeLayer, ("join_id",))
    pt_no_list = []
    for row in rows:
        pt_no_list.append(row[0])
    rows = arcpy.da.UpdateCursor(nodeLayer, ("SHAPE@", "join_id"))
    for row in rows:
        if row[1] <> -1:
            continue
        pt1 = row[0]
        for line in total_list:
            if func.compare_pt(pt1.labelPoint, line[0]) or func.compare_pt(pt1.labelPoint, line[1]):
                row[1] = the_other(line[2], line[3], pt_no_list)
                rows.updateRow(row)
                print str(row[1])+"  update"
                break

main2()