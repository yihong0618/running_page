import duckdb

with duckdb.connect() as conn:
    conn.install_extension("sqlite")
    conn.load_extension("sqlite")
    conn.sql("ATTACH 'run_page/data.db' (TYPE SQLITE);USE data;")
    conn.sql(
        "COPY (SELECT * FROM activities) TO 'run_page/data.parquet' (FORMAT PARQUET);"
    )

"""
examples:

duckdb.sql("select regexp_extract(location_country, '[\u4e00-\u9fa5]{2,}(市 | 自治州 | 特别行政区)') as run_location, concat(try_cast(sum(distance/1000) as integer)::varchar,' km') as run_distance from read_parquet('https://github.com/yihong0618/run/raw/refs/heads/master/run_page/data.parquet') where run_location is not NULL group by run_location order by sum(distance) desc;").show(max_rows=50)

┌──────────────┬──────────────┐
│ run_location │ run_distance │
│   varchar    │   varchar    │
├──────────────┼──────────────┤
│ 大连市       │ 9328 km      │
│ 沈阳市       │ 2030 km      │
│ 北京市       │ 61 km        │
│ 长沙市       │ 24 km        │
│ 扬州市       │ 21 km        │
│ 盘锦市       │ 21 km        │
│ 烟台市       │ 21 km        │
│ 上海市       │ 12 km        │
│ 北九州市     │ 7 km         │
│ 丹东市       │ 5 km         │
│ 瓦房店市     │ 4 km         │
│ 竹田市       │ 3 km         │
│ 伊万里市     │ 2 km         │
│ 长春市       │ 1 km         │
│ 锦州市       │ 1 km         │
│              │ 0 km         │
├──────────────┴──────────────┤
│ 16 rows           2 columns │
└─────────────────────────────┘

duckdb.sql("select start_date_local, distance, name, location_country from read_parquet('https://github.com/yihong0618/run/raw/refs/heads/master/run_page/data.parquet') order by run_id desc limit 1;")


duckdb.sql("select start_date_local[:4] as year, sum(distance/1000)::integer from read_parquet('https://github.com/yihong0618/run/raw/refs/heads/master/run_page/data.parquet') group by year order by year desc;").show(max_rows=50)

┌─────────┬─────────────────────────────────────────┐
│  year   │ CAST(sum((distance / 1000)) AS INTEGER) │
│ varchar │                  int32                  │
├─────────┼─────────────────────────────────────────┤
│ 2024    │                                    1605 │
│ 2023    │                                     696 │
│ 2022    │                                     758 │
│ 2021    │                                    1244 │
│ 2020    │                                    1284 │
│ 2019    │                                    1344 │
│ 2018    │                                     405 │
│ 2017    │                                     964 │
│ 2016    │                                     901 │
│ 2015    │                                     436 │
│ 2014    │                                     823 │
│ 2013    │                                     790 │
│ 2012    │                                     387 │
├─────────┴─────────────────────────────────────────┤
│ 13 rows                                 2 columns │
└───────────────────────────────────────────────────┘

duckdb.sql("SELECT concat(try_cast(distance/1000 as integer)::varchar,' km') as distance_km,count(*) FROM read_parquet('https://github.com/yihong0618/run/raw/refs/heads/master/run_page/data.parquet') GROUP BY distance_km order by count(*) desc;").show(max_rows=50)

┌─────────────┬──────────────┐
│ distance_km │ count_star() │
│   varchar   │    int64     │
├─────────────┼──────────────┤
│ 2 km        │          706 │
│ 3 km        │          639 │
│ 1 km        │          493 │
│ 5 km        │          391 │
│ 4 km        │          337 │
│ 6 km        │          164 │
│ 10 km       │           84 │
│ 8 km        │           55 │
│ 7 km        │           54 │
│ 0 km        │           29 │
│ 12 km       │           25 │
│ 11 km       │           17 │
│ 9 km        │           17 │
│ 15 km       │           15 │
│ 21 km       │            8 │
│ 16 km       │            7 │
│ 14 km       │            6 │
│ 20 km       │            6 │
│ 17 km       │            4 │
│ 18 km       │            3 │
│ 19 km       │            2 │
│ 13 km       │            2 │
│ 43 km       │            2 │
│ 24 km       │            1 │
│ 41 km       │            1 │
│ 28 km       │            1 │
├─────────────┴──────────────┤
│ 26 rows          2 columns │
└────────────────────────────┘
"""
