from sqlalchemy import create_engine
import pandas as pd
import os


def get_gde_url(country:str = None):
    if country is None:
        sql_statement = 'select url, name_de from municipality;'
    else:
        sql_statement = f"""
        SELECT m.url, m.name_de 
        FROM municipality AS m
        JOIN state ON state.id = m.state_id
        JOIN country ON state.country_code = country.code
        WHERE country.name_en = '{country}';
        """
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
        # host = 'localhost'
        # port = '5500'
    user = 'digilog'
    password = 'password'
    database = 'digilog'

    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'

    engine = create_engine(connection_string)

    result = engine.execute(sql_statement)

    columns_crawl = ['url', 'gdename']
    df = pd.DataFrame(result, columns=columns_crawl)
    return df