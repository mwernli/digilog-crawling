import pandas as pd
from getData import get_data_wikipedia
import progressbar
# import psycopg2
# from psycopg2.extras import execute_values
from sqlalchemy import create_engine


INSERT_DB = True

# host = 'localhost'
host = 'digilog-postgres'
# port = '5500'
port = '5432'
user = 'digilog'
password = 'password'
db = 'digilog'
schema = 'digilog'


df_ch = pd.read_excel(
    'data/Gemeindeliste.xlsx',
    sheet_name='GDE'
)

if __name__ == '__main__':
    locality_arr = df_ch.GDENAME.values
    ch_dict = {}
    for i in progressbar.progressbar(range(len(locality_arr))):
    # for i in progressbar.progressbar(range(10)):
        #status
        #0 : all good
        #1 : no page existing
        #2 : no connection to existing page
        #3 : only wikipedia page callable
        #4 : no home page avaliable
        #5 : could not extract population
        #6 : could not extract elevation
        #7 : could not extract area
        url, status, area, population, elevation, postalCode, longitude, latitude = get_data_wikipedia(locality_arr[i])
        if status == 1 or status == 2:
            url, status, area, population, elevation, postalCode, longitude, latitude = get_data_wikipedia(locality_arr[i] +'_' + df_ch['GDEKT'].values[i])

        if longitude is None or latitude is None:
            longitude, latitude = 0, 0
        ch_dict[locality_arr[i]] = {
            'id': i,
            'url' : url,
            'status': status,
            'latitude_n': latitude,
            'longitude_e': longitude,
            'population': population,
            'elevation': elevation,
            'area' : area,
            'postalCode' : postalCode
        }
        for j in range(len(df_ch.columns.values)):
            ch_dict[locality_arr[i]][df_ch.columns.values[j].lower()] = str(df_ch[df_ch.columns.values[j]].iloc[i])

        keys = list(ch_dict[locality_arr[i]].keys())
        values = tuple(ch_dict[locality_arr[i]].values())

        update_string = ''
        for n in range(len(keys)):
            update_string += keys[n] + ' = excluded.' + keys[n] + ', '
        if INSERT_DB:

            connection_string = f'postgresql://{user}:{password}@{host}:{port}/{db}'
            engine = create_engine(connection_string)


            with engine.connect() as connection:
                connection.execute(
                    f'''
                    INSERT INTO loc_gov_ch (id, url, status, latitude_n, longitude_e, population, elevation, area, postalCode, gdekt, gdebznr, gdenr, gdename, gdenamk, gdebzna, gdektna, gdemutdat)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE 
                        SET {update_string[:-2]};
                    ''', tuple(ch_dict[locality_arr[i]].values())
                )
            connection.close()

        else:
            df = pd.DataFrame(ch_dict).transpose()
            df.to_csv('/data/wikipedia_info_ch_db.csv')

