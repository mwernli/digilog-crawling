# from importlib.machinery import SourceFileLoader
# module, path = 'DataSource', '/home/ubuntu/digilog/digilog-crawling/scrapy/digilog/digilog/DataSource.py'
# DataSource = SourceFileLoader(module,path).load_module()
import pandas as pd
import psycopg2

# host = 'digilog-postgres'
# host = '172.19.0.3'
host = 'localhost'
port = '5500'
user = 'digilog'
password = 'password'
db = 'digilog'
schema = 'digilog'

def postgres_call(sql_statement):
    connection = psycopg2.connect(
        dbname=db,
        user=user,
        password=password,
        host=host,
        port=port
    )

    #sql_statement = 'select * from crawl'
    cursor = connection.cursor()
    cursor.execute(sql_statement)
    result = cursor.fetchall()
    connection.close()
    return result

columns_crawl = ['id', 'inserted_at', 'top_url']
sql_statement_crawl = 'select * from crawl;'
result_crawl = postgres_call(sql_statement_crawl)

df_crawl = pd.DataFrame(result_crawl, columns = columns_crawl).set_index('id')
print(df_crawl)


column_crawl_result = ['id', 'insert_at', 'crawl_id', 'url', 'link_text', 'parent', 'mongo_id']
sql_statement_crawl_result = 'select * from crawl_result where crawl_id = 7;'
result_crawl_result = postgres_call(sql_statement_crawl_result)

df_crawl_result = pd.DataFrame(result_crawl_result, columns = column_crawl_result).set_index('id')
print(df_crawl_result)