from sqlalchemy import create_engine
import pandas as pd

def get_crawl_table():
    host = 'digilog-postgres'
    port = '5432'
    user = 'digilog'
    password = 'password'
    database = 'digilog'

    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'

    engine = create_engine(connection_string)

    result = engine.execute('select * from crawl;')
    columns_crawl = ['id', 'inserted_at', 'top_url']
    df = pd.DataFrame(result, columns=columns_crawl).set_index('id')
    return df.to_html()
