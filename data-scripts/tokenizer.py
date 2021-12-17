import sys

punctuation = [
    ',', '%', '-', '.', '?', '!', '(', ')', '/', ';', ':', '"', "'", '*', '&', '^', '$', '@', '<', '>', '[', ']', '|', '\\', '+', '~', '`',
    '%', 
]

with open(sys.argv[1], 'r') as to_tokenize:
    with open(sys.argv[2], 'w') as output:
        for line in to_tokenize:
            for p in punctuation:
                line = line.replace(p, f' {p} ')
            output.write(line)
