import workqueue as wq

for year in range(2000, 2022):
    for month in range(1, 13):
        t = wq.task("python scrape_day.py {year}{month:02}")
        t.specify_output_file("{year}{month:02}.csv")
        q.queue(t)
while not q.empty():
    q.wait()
