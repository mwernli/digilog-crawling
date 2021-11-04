from sqlalchemy import create_engine
import pandas as pd
import os


def get_gde_url():
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

    result = engine.execute('select url, gdename from loc_gov_ch;')

    columns_crawl = ['url', 'gdename']
    df = pd.DataFrame(result, columns=columns_crawl)
    return df