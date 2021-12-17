import re

def generic_headline(pbp):
    score = pbp.split('\t')[0].split("Final score : ")[1]
    res = re.match(r'(.*) (\d+) - (.*) (\d+)', score)
    offset = (int(res.group(2)) < int(res.group(4))) * 2
    headline = f'{res.group(offset + 1)} beat {res.group((offset + 2) % 4 + 1)} , {res.group(offset + 2)} - {res.group((offset + 3) % 4 + 1)}'
    return headline


if __name__ == "__main__":
    import sys
    collection_file = sys.argv[1] #'/scratch365/tfisher4/nlp-proj/pbp-to-headline/tokenized/test.pbp'
    with open(collection_file) as pbps:
        for pbp in pbps:
            print(generic_headline(pbp))

