import os
import re
from pathlib import Path

tokenized_data_root = '/scratch365/tfisher4/nlp-proj/pbp-to-headline/tokenized/'
big_file_output = '/scratch365/tfisher4/nlp-proj/pbp-to-headline/tokenized/collection.data'

def get_game_and_id(fpath):
    with open(fpath) as f:
        game = f.read()
    if len(game) <= 1: return None, None
    #print(game)
    score = game.split('\t')[0].split("Final score : ")[1]
    res = re.match(r'(.*) \d+ - (.*) \d+', score)
    game_id = f'{res.group(1)}{res.group(2)}{fpath.name}'
    return game, game_id 

if __name__ == "__main__":
    curr_year = None
    games_seen_in_year = None
    with open(big_file_output, 'w') as out:
        for root, dirs, files in os.walk(tokenized_data_root):
            for fname in files:
                fpath = Path(os.path.join(root, fname))
                year = fpath.parents[1].name
                if curr_year is None or year != curr_year:
                    games_seen_in_year = set()
                    curr_year = year
                    print(curr_year)
                game, game_id = get_game_and_id(fpath)
                if game_id is None or game_id in games_seen_in_year:
                    continue
                games_seen_in_year.add(game_id)
                out.write(game if game.endswith('\n') else game + '\n')
