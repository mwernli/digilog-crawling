from sqlalchemy import create_engine
import pandas as pd


host = 'digilog-postgres'
port = '5432'
user = 'digilog'
password = 'password'
database = 'digilog'

connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'

engine = create_engine(connection_string)

result = engine.execute('select * from crawl;')

df = pd.DataFrame(result)
