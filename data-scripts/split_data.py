import sys
import os

input_dir = sys.argv[1]
output_dir = sys.argv[2]

train = open(os.path.join(output_dir, 'train'), 'w')
dev = open(os.path.join(output_dir, 'dev'), 'w')
test = open(os.path.join(output_dir, 'test'), 'w')

counter = 0
dev_set = {5, 15}
test_set = {3, 10, 17}

for fileentry in os.scandir(input_dir):
    with open(fileentry.path) as f:
        lines = iter(f)
        for pbp_line in lines:
            summ_line = next(lines)
            if counter in dev_set: dev.write(pbp_line + summ_line)
            elif counter in test_set: test.write(pbp_line + summ_line)
            else: train.write(pbp_line + summ_line)
            counter = (counter + 1) % 20

train.close()
dev.close()
test.close()
