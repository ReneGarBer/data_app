import abc
import ee
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class DBConnector(abc.ABC):
    def __init__(self, config):
        self.config = config
        self.connection = None

    @abc.abstractmethod
    def get_connection(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def test_connection(self):
        pass

    @abc.abstractmethod
    def configure(self,config:dict):
        pass

class PostgresConnector(DBConnector):
    def __init__(self, config):
        super().__init__(config)
        self.url = f"{config.get('con_type')}+psycopg2://{config.get('db_user')}:" \
                f"{config.get('db_password')}@{config.get('db_host')}:{config.get('db_port')}" \
                f"/{config.get('db_name')}"
        self.engine: Engine = None
        self.connection = None
        self.db_name = config.get('db_name')
      


    def get_connection(self):
        try:
            self.engine = create_engine(self.url)
            self.connection = self.engine.connect()
            return self.connection
        
        except SQLAlchemyError as e:
            raise e

    def close(self):
        if self.connection:
            self.connection.close()
        return "Conexion a la base de datos cerrada"
    
    def test_connection(self):
        try:
            self.engine = create_engine(self.url)
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT version();"))
                for row in result:
                    print("Versión de PostgreSQL:", row[0])
                    
        except Exception as e:
            print("❌ Error al conectar:", str(e))

    def configure(self,config:dict):
        self.table = config.get('table')
        self.schema = config.get('schema')

class EEConnector():
    def __init__(self,credentials):
        self.credentials = dict(credentials)
        self.filters: dict = None
        self.bands = None
        self.dataset = None
        self.cadence = None
        self.batch: dict = None
        self.window = None
        self.dataset = None
        self.map = None
        return None

    def configure(self,config: dict):
        self.bands = config.get("bands")
        self.cadence = config.get("source")['cadence']
        self.dataset = config.get("source")['dataset']
        self.filters = config.get("filters")
        self.batch = config.get("batch")
        self.map = config.get('map')

    def initialize_connection(self):
        try:
            credentials = ee.ServiceAccountCredentials(self.credentials['service_account'],self.credentials['key_path'])
            ee.Initialize(credentials=credentials)
            print("Conexion exitosa a Google Earth API:")
        except Exception as e:
            print("❌ Error al conectar:", str(e))

    def _get_data(self,region,date):
        geografia = region.map(lambda feature: feature.geometry())

        data = (ee.ImageCollection(self.dataset)
            .filter(date)
            .filterBounds(geografia)
            .select(self.bands)
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
        
    def _get_region_filter(self):
        column = list(self.filters.get('region')['municipios'].keys())[0]
        estado = list(self.filters.get('region')['estado'].values())[0]
        
        for subregion in self.filters.get('region')['municipios'][column]:
            if '-' in subregion:
                start_str, end_str = subregion.split('-')
                start, end = int(start_str), int(end_str)
                for num in range(start, end + 1):
                    value = f"{estado}{num:03}"
                    yield (ee.FeatureCollection(self.filters['region']['asset']).filter(ee.Filter.eq(column,value)),f"{column}:{value}")
            
            else:
                value = f"{estado}{subregion}"
                yield (ee.FeatureCollection(self.filters['region']['asset']).filter(ee.Filter.eq(column,value)),f"{column}:{value}")
    
    def _get_time_filters(self):
        start_date,end_date = (
            datetime.strptime(self.filters.get('dates')['desde'], "%Y-%m-%d"), 
            datetime.strptime(self.filters.get('dates')['hasta'] , "%Y-%m-%d")
        )

        current_date = start_date

        while current_date < end_date:
            next_date = current_date + relativedelta(
                years=self.batch["window"]["years"],
                months=self.batch["window"]["months"],
                days=self.batch["window"]["days"]
            )

            if next_date > end_date:
                next_date = end_date
            
            yield (ee.Filter.date(current_date,next_date),f"desde:{current_date}\thasta:{next_date}")

            current_date = next_date    
    
    def get_data(self):
        try:
            log_data: str = None
            if self.batch.get('subregion') and self.batch.get('time'):
                for region, region_logs in self._get_region_filter():
                    dates = self._get_time_filters()
                    for date, time_logs in dates:
                        log_data = f"{time_logs}\t{region_logs}"
                        data = self._get_data(region,date)
                        df = self._to_dataframe(data,region)
                        #return a tuple with (df,log_data)
                        yield (df,log_data)

            elif self.batch.get('subregion') and not self.batch.get('time'):
                date = ee.Filter.date(self.filters['dates']['desde'],self.filters['dates']['hasta'])
                time_logs = f"desde:{self.filters['dates']['desde']}\thasta:{self.filters['dates']['hasta']}"
                for region, region_logs in self._get_region_filter():
                    log_data = f"{time_logs}\t{region_logs}"
                    data = self._get_data(region,date)
                    df = self._to_dataframe(data,region)
                    #return a tuple with (df,log_data)
                    yield (df,log_data)
            elif self.batch.get('time'):
                column = list(self.filters.get('region')['estado'].keys())[0]
                value = f"{self.filters.get('region')['estado'][column]}000"
                region_logs = f"{column}:{value}"
                region = ee.FeatureCollection(self.filters['region']['asset']).filter(ee.Filter.eq(column,value))
                dates = self._get_time_filters()
                for date, time_logs in dates:
                    log_data = f"{time_logs}\t{region_logs}"
                    data = self._get_data(region,date)
                    df = self._to_dataframe(data,region)
                    #return a tuple with (df,log_data)
                    yield (df,log_data)
            else:
                date = ee.Filter.date(self.filters['dates']['desde'],self.filters['dates']['hasta'])
                time_logs = f"desde:{self.filters['dates']['desde']}\thasta:{self.filters['dates']['hasta']}"
                
                column = list(self.filters.get('region')['estado'].keys())[0]
                value = f"{column}:{self.filters.get('region')['estado'][column]}000"
                region_logs = f"{column}:{value}"
                region = ee.FeatureCollection(self.filters['region']['asset']).filter(ee.Filter.eq(column,value))

                log_data = f"{time_logs}\t{region_logs}"

                data = self._get_data(region,date)
                df = self._to_dataframe(data,region)
                #return a tuple with (df,log_data)                
                yield (df,log_data)

        except Exception as e:
            raise f"get_data: {e} con variables: {log_data}"
            
    def _to_dataframe(self,data,regions):
        def compute(img):
            region = regions.map(lambda f: f.set('fecha', img.get('fecha'),'start', img.get('start'),'end', img.get('end')))
            reduced = img.reduceRegions(
                collection=region,
                reducer=ee.Reducer.mean()
            ).select(list(self.map.keys()))
            return reduced

        expression = data.map(compute).flatten()

        df = ee.data.computeFeatures({
        'expression':expression,
        'fileFormat':'PANDAS_DATAFRAME'
        })
        return df