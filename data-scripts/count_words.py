from hw2_transformer import read_parallel, progress
import sys
filename = sys.argv[1]

max_pbp = 0
max_headline = 0
#with open(filename) as f:
for pbp, headline in progress(read_parallel(filename)):
    max_pbp = max(max_pbp, len(pbp))
    max_headline = max(max_headline, len(headline))

print(max_pbp, max_headline)
