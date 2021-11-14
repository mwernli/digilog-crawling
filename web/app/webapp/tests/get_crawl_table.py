from sqlalchemy import create_engine
import pandas as pd
import os

def get_crawl_table():
    try:
        if bool(int(os.environ['OUTSIDE_NETWORK'])):
            host = 'localhost'
            port = '5500'
        else:
            host = 'digilog-postgres'
            port = '5432'
    except KeyError:
        host = 'digilog-postgres'
        port = '5432'
    user = 'digilog'
    password = 'password'
    database = 'digilog'

    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'

    engine = create_engine(connection_string)

    result = engine.execute('select * from crawl;')
    # columns_crawl = ['id', 'inserted_at', 'top_url']
    # df = pd.DataFrame(result, columns=columns_crawl)#.set_index('id')
    # return df.style.hide_index().to_html()
    # return result.fetchall()
    columns_crawl = ['id', 'inserted_at', 'top_url']
    df = pd.DataFrame(result, columns=columns_crawl)#.set_index('id')
    return [df.iloc[i,:].to_dict() for i in range(df.shape[0])]
