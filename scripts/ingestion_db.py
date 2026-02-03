print(">>> ingestion_db module started")

import pandas as pd
import os
from sqlalchemy import create_engine
import logging
import time

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename= "logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

engine= create_engine('sqlite:///inventory.db')

print(">>> defining ingest_db")
def ingest_db(df, table_name, engine):
    '''this function will ingest dataframe into database table'''
    df.to_sql(table_name, con = engine, if_exists= 'replace', index=False)
print(">>> ingestion_db module finished")

def load_raw_data():
    '''this function will load the csv files as dataframe and ingest into db'''
    start= time.time()
    for file in os.listdir('vendor_data'):
        if file in os.listdir('vendor_data'):
            df=pd.read_csv('vendor_data/'+file)
            logging.info(f'Ingesting {file} in db')
            ingest_db(df,file[:-4], engine)
    end= time.time()
    total_time= (end - start)/60
    logging.info('---------Ingestion Complete-----------')

    logging.info(f'\n Total Timr Taken: {total_time} minutes')

if __name__=='__main__':
    load_raw_data()