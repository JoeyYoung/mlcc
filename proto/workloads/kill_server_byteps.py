import os

pid_lines = os.popen("ps -ef | grep byteps.server").readlines()

for line in pid_lines:
    elems = line.split(' ')
    for elem in elems:
        if elem == '' or elem == 'xyzhao':
            continue
        pid = int(elem)
        os.system("kill " + "-9 " + str(pid))
        break


