
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime
from configuration import Configuration
from logs import logs
import ee
import pandas as pd
from sqlalchemy import create_engine, URL
import psycopg2

class EEpipelines:

    def __init__(self,config: Configuration, credentials: dict):
        self.config = config        
        self.credentials = credentials 
    
    def __str__(self):
        return None
    
    def run_pipeline_csv(self):
        try:
            if self.config.batch["lote"]["time"]:
                self.process_dates()
            else:
                column = list(self.config.region['estado'].keys())[0]
                estado = self.config.region['estado'][column]

                if self.config.batch["lote"]["subregion"]:
                    self.process_subregion(self.config.dates['desde'],self.config.dates['hasta'],estado)
                else:
                    
                    self.pipeline_to_csv(column,estado,self.config.dates['desde'],self.config.dates['hasta'],logfile=self.config.logs)

        except Exception as e:
            return e

    def connect(self):
        credentials = ee.ServiceAccountCredentials(self.credentials['eeAPI']['service_account'],self.credentials['eeAPI']['key_path'])
        ee.Initialize(credentials=credentials)

    @logs
    def pipeline_to_csv(self,column,value,desde,hasta,logfile=None):
        try:
            self.connect()
            region = self.get_region(column,value)
            data = self.get_data(desde,hasta,region)
            df = self.to_dataframe(data,region)
            df.drop(self.config.drop, inplace=True,axis=1)
            path = f"{self.config.target}{self.config.name}{self.config.dates['desde']}_{self.config.dates['hasta']}.csv"
            columns = list(self.config.map.keys())            
            df.to_csv(path_or_buf=path,columns=columns,header=False,mode='a',index=self.config.index)
            message = f"desde:{desde}\thasta:{hasta}\t{column}:{value}\tTermino con exito"
            return message
        except Exception as e:
            return e
        
    def get_data(self,desde: str, hasta: str,region):

        geografia = region.map(lambda feature: feature.geometry())

        data = (ee.ImageCollection(self.config.source["dataset"])
            .filter(ee.Filter.date(desde,hasta))
            .filterBounds(geografia)
            .select(self.config.bands)
            .map(lambda image: image.set(
                        {
                        'fecha': image.get('system:index'),
                        'start': image.get('system:time_start'),
                        'end': image.get('system:time_end')
                        }
                    )
                )
            )
        return data

    def get_region(self,column,value):
        return ee.FeatureCollection(self.config.region['asset']).filter(ee.Filter.eq(column,value))

    def to_dataframe(self,data,feature):
        def compute(img):
            features = feature.map(lambda f: f.set('fecha', img.get('fecha'),'start', img.get('start'),'end', img.get('end')))
            regions = img.reduceRegions(
                collection=features,
                reducer=ee.Reducer.mean()
            ).select(list(self.config.map.keys()))
            return regions

        expression = data.map(compute).flatten()

        df = ee.data.computeFeatures({
        'expression':expression,
        'fileFormat':'PANDAS_DATAFRAME'
        })

        return df
    
    def process_subregion(self,desde,hasta,region):
        column = list(self.config.region['municipios'].keys())[0]
        for subregion in self.config.region['municipios'][column]:
            if '-' in subregion:
                start_str, end_str = subregion.split('-')
                start, end = int(start_str), int(end_str)
                for num in range(start, end + 1):
                    value = f"{region}{num:03}"
                    self.pipeline_to_csv(column,value,desde,hasta,logfile=self.config.logs)
            
            else:
                value = f"{region}{subregion}"
                self.pipeline_to_csv(column,value,desde,hasta,logfile=self.config.logs)    
    
    def process_dates(self):

        start_date,end_date = (
            datetime.strptime(self.config.dates['desde'], "%Y-%m-%d"), 
            datetime.strptime(self.config.dates['hasta'] , "%Y-%m-%d")
        )

        current_date = start_date

        while current_date < end_date:
            next_date = current_date + relativedelta(
                years=self.config.batch["time"]["years"],
                months=self.config.batch["time"]["months"],
                days=self.config.batch["time"]["days"]
            )

            if next_date > end_date:
                next_date = end_date

            estado = list(self.config.region['estado'].values())[0]
            if self.config.batch["lote"]["subregion"]:
                self.process_subregion(current_date,next_date,estado)

            else:
                column = list(self.config.region['estado'].keys())[0]
                self.pipeline_to_csv(column,estado,current_date,next_date,logfile=self.config.logs)

            current_date = next_date

    @logs
    def pipeline_to_db(self):
        try:
            engine = self.postgresql_engine()
            file = f"{self.config.target}{self.config.name}{self.config.dates['desde']}_{self.config.dates['hasta']}.csv"
            headers = list(self.config.map.values())
            df = pd.read_csv(file,header=None,names=headers)
            with engine.connect() as con:
                df.to_sql(name=self.config.table, con=con, schema="staging",if_exists='append', index=False)   
            message =( f"Archivo:{self.config.name}{self.config.dates['desde']}_{self.config.dates['hasta']}.csv"
                f"se cargo con exito Termino con exito")
            return message 
        except Exception as e:
            return f"error: {e}"
    
    def postgresql_engine(self):
        try:
            url =  URL.create(
                        "%s+%s"%("postgresql","psycopg2"),
                        username=self.credentials['postgresql']['db_user'],
                        password=self.credentials['postgresql']['db_password'],
                        host=self.credentials['postgresql']['db_host'],
                        database=self.credentials['postgresql']['db_name'],
                        port=self.credentials['postgresql']['db_port']
                    )

            engine = create_engine(url)
            return engine
        except Exception as e:
            return e