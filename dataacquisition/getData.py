import wikipedia
import pandas as pd
from bs4 import BeautifulSoup
import requests
#import lxml
import numpy as np
from rdflib import Graph
import SPARQLWrapper
from SPARQLWrapper import JSON, N3
from pprint import pprint
import re



def get_data_wikipedia(municipalty:str):
    area = 'NULL'
    population = 0
    elevation = 'NULL'
    postal_code = 'NULL'
    latitude = 0
    longitude = 0
    #get wikipdia url
    municipalty.replace('(', '').replace(')', '')
    try:
        url_link_wikipedia = wikipedia.page(f'{municipalty} ').url
    except wikipedia.exceptions.DisambiguationError:
        return ('no wikipedia page found', 1, area, population, elevation, postal_code, longitude, latitude)
    except wikipedia.exceptions.PageError:
        return ('no wikipedia page found', 1, area, population, elevation, postal_code, longitude, latitude)

    try:
        response = requests.get(url_link_wikipedia)
    except requests.exceptions.ConnectionError:
        return ('no connection to page', 2, area, population, elevation, postal_code, longitude, latitude)

    soup = BeautifulSoup(response.text, 'html.parser')
    #extract wikipedia table with website url
    table = soup.find('table', {'class':'infobox ib-settlement vcard'})
    try:
        postal_code = soup.find('div', {'class':'postal-code'}).text
    except:
        pass
    try:
        latitude_str = re.split(
            "°|′",
            soup.find('span', {'class':  'latitude'}).text
        )
        latitude = round(float(latitude_str[0]) + float(latitude_str[1]) / 60, 5)

        longitude_str = re.split(
            "°|′",
            soup.find('span', {'class':  'longitude'}).text
        )
        if longitude_str[-1] == 'E':
            longitude = round(float(longitude_str[0]) + float(longitude_str[1]) / 60, 5)
        else:
            longitude = round(float(longitude_str[0]) + float(longitude_str[1]) / 60, 5) * -1
    except:
        pass

    if table is None:
        local_gov_url = 'not a locality'
        return (url_link_wikipedia, 1, area, population, elevation, postal_code, longitude, latitude)
    else:
        df = pd.DataFrame(pd.read_html(str(table))[0])
        # extract website
        try:
            table_website = df.iloc[df.iloc[:,0].values == 'Website',1].values[0]
        except IndexError:
            return ('no homepage available', 4, area, population, elevation, postal_code, longitude, latitude)
        if table_website is np.nan :
            return (url_link_wikipedia, 3, area, population, elevation, postal_code, longitude, latitude)
        else:
            local_gov_url = table_website.split(' ')[0]
        # extract population
        try:
            rownames_df = df.iloc[:,0].values.astype(str)
            indices = np.array([ind for ind, s in enumerate(rownames_df) if 'Population' in s])[0]
            if df.iloc[:,0].values[indices] == df.iloc[:,1].values[indices]:
                population = df.iloc[:,1].values[indices + 1]
            else:
                population = df.iloc[:,1].values[indices]
        except:
            return (local_gov_url, 5, area, population, elevation, postal_code, longitude, latitude)

        # extract elevation
        try:
            rownames_df = df.iloc[:,0].values.astype(str)
            indices = np.array([ind for ind, s in enumerate(rownames_df) if 'Elevation' in s])[0]
            if df.iloc[:,0].values[indices] == df.iloc[:,1].values[indices]:
                elevation = df.iloc[:,1].values[indices + 1]
            else:
                elevation = df.iloc[:,1].values[indices]
        except:
            return (local_gov_url, 6, area, population, elevation, postal_code, longitude, latitude)
        # extract area
        try:
            rownames_df = df.iloc[:,0].values.astype(str)
            indices = np.array([ind for ind, s in enumerate(rownames_df) if 'Area' in s])[0]
            if df.iloc[:,0].values[indices] == df.iloc[:,1].values[indices]:
                area = df.iloc[:,1].values[indices + 1]
            else:
                area = df.iloc[:,1].values[indices]
        except:
            return (local_gov_url, 7, area, population, elevation, postal_code, longitude, latitude)


    return (local_gov_url, 0, area, population, elevation, postal_code, longitude, latitude)

def get_data_dbpedia(attr_dict:dict,
                     comm:str,
                     sparql:SPARQLWrapper.SPARQLWrapper):
    # status 0  : everything imported
    # status 1  : 1 attribute not imported
    # status 2  : 2 attributs not imported
    # status 10 : could not find dbpedia entry

    ch_dict  = {}

    #comm_vec = ['Hittnau']
    #for comm in comm_vec:
    ch_dict[comm] = {}
        #for attr in list(attirbute_dict.keys()):
    ch_dict[comm]['status'] = 0
    for attr in list(attr_dict.keys()):

        sparql.setQuery(f"""
            SELECT ?{attr}
            WHERE {{ dbr:{comm} {attr_dict[attr]} ?{attr} .}}
        """)
        sparql.setReturnFormat(JSON)
        try:
            qres = sparql.query().convert()
        except:
            ch_dict[comm][attr] = None
            ch_dict[comm]['status'] = 10
            continue
        try:
            ch_dict[comm][attr] = qres['results']['bindings'][0][attr]['value']
        except IndexError:
            ch_dict[comm][attr] = None
            ch_dict[comm]['status'] += 1
    return ch_dict


if __name__ == '__main__':
    print(get_data_wikipedia('Augsburg'))
