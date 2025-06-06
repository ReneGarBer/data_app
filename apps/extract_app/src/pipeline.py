from configuration import Configuration
from logs import logs
import pandas as pd
from connectores import *
from typing import Optional
class EEpipelines:

    def __init__(self,config: Configuration, source: Optional['Connector'], target: Optional['Connector']):
        self.config = config
        self.source = source
        self.target = target
    
    def __str__(self):
        return None
    
    @logs
    def run_sql(self):
        try:
            name = self.config["name"]
            start_date = self.config['filters']['dates']['desde']
            end_date = self.config['filters']['dates']['hasta']
            region = f"estado: {self.config['filters']['region']['estado']} - municipios:{self.config['filters']['region']['municipios']}"
            message = f"Inicia - pipeline:{name}\tregion:{region}\tdesde:{start_date} - hasta:{end_date}"

            yield message

            self.source.configure(self.config)
            self.source.initialize_connection()

            for data,logs in self.source.get_data():
                if 'drop' in self.config.keys():
                    data.drop(columns=self.config['drop'],inplace = True)
                
                if 'map' in self.config.keys():
                    data.rename(columns=self.config['map'],inplace= True)

                data.to_csv(
                    f"{self.config['folder']}{name}{start_date}-{end_date}.csv",
                    mode='a',
                    index=self.config['index'] == "True"
                    )
                
                self.target.configure(self.config.get('target'))
                
                with  self.target.get_connection() as connection:
                    data.to_sql(
                        name = self.target.table,
                        con = connection,
                        schema = self.target.schema,
                        if_exists = 'append',
                        index=self.config['index'] == "True"
                        )

                yield f"{logs} Termino con exito"
                
        except KeyError as keyerror:
            raise ValueError(f"{keyerror}\npipeline:{name}\t{logs}")
        
        except SQLAlchemyError as sqlerror:
            raise ValueError(f"{sqlerror}\npipeline:{name}\t{logs}")
        
        except Exception as e:
            raise ValueError(f"{e}\npipeline:{name}\t{logs}")

    @logs
    def run_csv(self):
        try:
            name = self.config["name"]
            start_date = self.config['filters']['dates']['desde']
            end_date = self.config['filters']['dates']['hasta']
            region = f"estado: {self.config['filters']['region']['estado']} - municipios:{self.config['filters']['region']['municipios']}"
            message = f"Inicia - pipeline:{name}\tregion:{region}\tdesde:{start_date} - hasta:{end_date}"

            yield message

            file_path = f"{self.config['folder']}{name}{start_date}-{end_date}.csv"

            data = pd.read_csv(
                filepath_or_buffer=file_path,
                header=0
                )
            self.target.configure(self.config.get('target'))
            
            with  self.target.get_connection() as connection:
                data.to_sql(
                    name = self.target.table,
                    con = connection,
                    schema = self.target.schema,
                    if_exists = 'append',
                    index=self.config['index'] == 'True'
                    )
            log_info = f"carga de {file_path} a database:{self.target.db_name} {self.target.table}.{self.target.schema}"
            
            yield log_info

        except Exception as e:
            raise ValueError(f"{e}\npipeline:{name}\t{logs}")