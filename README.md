# nlp-project

This repo contains some files that weren't actually used for the final product. We will highlight the important ones.

Scripts used to collect and pre-process data found in `data-scripts`. Of importance:
  - `data-scripts/scrape_pbp_to_headline.py`: used to collect the data in `data/rich-pbp-to-headline/raw`. With slight modifications (I was dumb and modified in-place instead of creating a copy), can be used to collect the data in `data/pbp-to-headline/raw`
  - `data-scripts/scrape_mgr.py`: launches a WorkQueue manager that creates tasks to collect data by month. Used for parallel data collection
  - `data-scripts/tokenize_pbp.py`: tokenized all pbp data (produced `data/pbp-to-headline/tokenized` and `data/rich-pbp-to-headline/tokenized`
  - `data-scripts/split_pbp_data.py`: splits data deterministically into train (~75%), dev (~10%), and test (~15%). Used to produce the dev, and test files in `data/{rich-,}pbp-to-headline/tokenized` (train is not included in the repo because it exceeds GitHub's file size).
  - `data-scripts/{bbref_scrape_comment.py,html_scrape_day.py}`: collected data for the original stat-csv-to-full-recap concept that was abandoned. Included for completeness and posterity.

Python programs used to do nlp sutff in `nlp-scripts`. Of importance:
  - `baseline.py`: the baseline model
  - `nlp-scripts/hw2_transformer.py`: trained the basic transformer
  - `nlp-scripts/hw2_transformer_v2.py`: trained the expanded and rich play-by-play transformers
  
Data included in repo:
  - `data/pbp-to-headline`: play-by-play to headline data collected for training basic and expanded transformers, and fed to baseline to compute results. Includes raw collected data under `raw` and tokenized data under `tokenized`. The latter also includes the dev and test data used. Train data is not included because the file size exceeded 100 MB. Entire collection of tokenized data is 190 MB containing 43689 sentence pairs. Structured by year, and then by team, and then by month, and then by day. Includes scraper's error logs so you can know which days were not successful in being collected.
  - `data/rich-pbp-to-headline`: rich play-by-play to headline data collected for training rich play-by-play transformer. Includes raw collected data under `raw` and tokenized data under `tokenized`. The latter also includes the dev and test data used. Train data is not included because the file size exceeded 100 MB. Entire collection of tokenized data is 182 MB containing 40240 sentence pairs. Note that this is slightly smaller because it excludes all postseason data. Structured by year, and then by month. Includes scraper's error logs so you can know which days were not successful in being collected.
  - `data/csv-to-recap`: statistical csv to full recap data originally collected but later abandoned. Raw and tokenized data both included. Structured by month. Included for completeness and posterity.
  
 Trained models, along with their training output and test headlines, are included under `models/`.
