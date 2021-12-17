import sys

with open(sys.argv[1], 'r') as i:
    with open(sys.argv[2], 'w') as o:
        for line in i:
            o.write(i.split('\t')[sys.argv] + '\n')
