import sys
import os

input_file = sys.argv[1]
output_dir = sys.argv[2]

train = open(os.path.join(output_dir, 'train'), 'w')
dev = open(os.path.join(output_dir, 'dev'), 'w')
test = open(os.path.join(output_dir, 'test'), 'w')

# divide (deterministically) into roughly 10% dev, 15% test, 75% train
counter = 0
dev_set = {5, 15}
test_set = {3, 10, 17}

with open(input_file) as f:
    for line in f:
        (   dev if counter in dev_set
            else test if counter in test_set
            else train
        ).write(line)
        counter = (counter + 1) % 20

train.close()
dev.close()
test.close()
