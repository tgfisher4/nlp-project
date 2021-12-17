import work_queue as wq
from scrape_pbp_to_headline import scrape_month

q = wq.WorkQueue(name="nlp-data-collection-tfisher4-2")
tasks = {}
for year in range(2000, 2022):
    for month in range(4, 11):
        #t = wq.task("python scrape_day.py {year}{month:02} /scratch365/tfisher4")
        #t.specify_output_file("/scratch365/tfisher4/nlp-data/{year}{month:02}.csv")
        yearmonth = f"{year}{month:02}"
        t = wq.PythonTask(scrape_month, year, month, "/scratch365/tfisher4/nlp-proj/rich-pbp-to-headline/raw", True)
        t.specify_environment("scraper-chromeless.tar.gz")
        t.specify_input_file("scrape_pbp_to_headline.py", cache=True)
        #t.specify_input_file("bbref_scrape_comment.py")
        tid = q.submit(t)
        print(f"[{tid}] Submitted {yearmonth}")
        tasks[tid] = yearmonth

while not q.empty():
    t = q.wait()
    print(f"[{t.id}]: {tasks[t.id]} finished with {t.output}")
