import spacy
import sys
from functools import reduce
import os
from pathlib import Path

#punctuation = [ ',', '%', '-', '.', '?', '!', '(', ')', '/', ';', ':', '"', "'", '*', '&', '^', '$', '@', '<', '>', '[', ']', '|', '\\', '+', '~', '`', ]

module = "en_core_web_sm"
tokenizer = spacy.load(module).tokenizer

# lazily hard-coding for now, maybe change later... 
data_src_root = "/scratch365/tfisher4/nlp-proj/rich-pbp-to-headline/raw"
data_dst_root = "/scratch365/tfisher4/nlp-proj/rich-pbp-to-headline/tokenized"

for root, dirs, files in os.walk(data_src_root):  # Loop though directies recursively 
    # os.walk allows you to prune its recursive walk by modifying dirs in-place
    dirs[:] = [d for d in dirs if d != "error_logs"] # exclude error logs
    for fname in files:
        src_path = os.path.join(root, fname) # full path of file found
        dst_path = src_path.replace('raw', 'tokenized')
        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        with open(src_path, 'r') as i:
            with open(dst_path, 'w') as o:
                lines = []
                for line in i:
                    pbp, headline = line.split('\t')
                    tokenized_pbp = ' '.join(token.text for token in tokenizer(pbp))
                    tokenized_headline = ' '.join(token.text for token in tokenizer(headline))
                    lines.append(tokenized_pbp + '\t' + tokenized_headline)
                text = "\n".join(lines)
                #print(f'{text} to {dst_path})')
                o.write(text)



"""
with open(sys.argv[1], 'r') as to_tokenize:
    with open(sys.argv[2], 'w') as output_f:
        lines = iter(to_tokenize)
        for csv_line in lines: 
            recap_line = next(lines)

            processed_csv_line = reduce(lambda line, p: line.replace(p, f' {p} '), punctuation, csv_line)
            processed_recap_line = ' '.join(token.text for token in tokenizer(recap_line))

            output_f.write(processed_csv_line)
            output_f.write(processed_recap_line)
            next(lines)
        output_f.write(' '.join(token.text for token in tokenizer(to_tokenize.read())))
"""
