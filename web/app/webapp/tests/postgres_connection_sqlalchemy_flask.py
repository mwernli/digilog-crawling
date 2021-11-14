import os
from sqlalchemy import create_engine
import pandas as pd

def get_connection_string(db = 'postgres'):
    if db = 'postgres':
        try:
            if bool(int(os.environ['OUTSIDE_NETWORK'])):
                host = 'localhost'
                port = '5500'
        except KeyError:
            host = 'digilog-postgres'
            port = '5432'
        user = 'digilog'
        password = 'password'
        database = 'digilog'

        connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        # engine = create_engine(connection_string)
        #
        # result = engine.execute('select * from crawl;')
        # print(pd.DataFrame(result))
        #return pd.DataFrame(result)
        return connection_string
    elif db_table == 'mongodb':
        pass
