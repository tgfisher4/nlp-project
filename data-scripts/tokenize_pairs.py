import spacy
import sys
from functools import reduce

punctuation = [ ',', '%', '-', '.', '?', '!', '(', ')', '/', ';', ':', '"', "'", '*', '&', '^', '$', '@', '<', '>', '[', ']', '|', '\\', '+', '~', '`', ]

module = "es_core_news_sm" if len(sys.argv) > 3 and sys.argv[3] == "Spanish" else "en_core_web_sm"
tokenizer = spacy.load(module).tokenizer
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
