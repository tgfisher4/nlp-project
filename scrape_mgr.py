import work_queue as wq
from html_scrape_day import scrape_month

q = wq.WorkQueue(name="nlp-data-collection-tfisher4")
for year in range(2000, 2022):
    for month in range(1, 13):
        #t = wq.task("python scrape_day.py {year}{month:02} /scratch365/tfisher4")
        #t.specify_output_file("/scratch365/tfisher4/nlp-data/{year}{month:02}.csv")
        t = wq.PythonTask(scrape_month, f"{year}{month:02}", "/scratch365/tfisher4")
        t.specify_environment("scraper-chromeless.tar.gz")
        t.specify_input_file("html_scrape_day.py")
        t.specify_input_file("bbref_scrape_comment.py")
        tid = q.submit(t)
        print(f"[{tid}] Submitted {year}{month:02}")
while not q.empty():
    t = q.wait()
    print(f"[{t.id}]: {t.output}")
