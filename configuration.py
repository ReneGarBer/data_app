import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Configuration:

    def __init__(self,config):      
        self.name = config["name"]
        self.description = config["description"]
        self.source = config["source"]
        self.dates = self.calculate_dates(config["filters"]["dates"])
        self.region = config["filters"]["region"]
        self.bands = config["bands"]
        self.map = config["map"]
        self.drop = config["drop"]
        self.index = config["index"] == "True"
        self.target = config["target"]
        self.logs = config["logs"]
        self.batch = config["batch"]
        self.batch["lote"]["time"] = self.batch["lote"]["time"] ==  "True"
        self.batch["lote"]["subregion"] = self.batch["lote"]["subregion"] == "True"
        return None

    def __str__(self):
        return (
            f"Pipeline configuration"
            f"  name: {self.name},\n"
            f"  description: {self.description},\n"
            f"  source: {self.source},\n"
            f"  filters: dates: {self.dates}, region: {self.region}\n"
            f"  bands: {self.bands},\n"
            f"  map: {self.map}\n"
            f"  drop: {self.drop},\n"
            f"  index: {self.index},\n"
            f"  target: {self.target},\n"
            f"  logs: {self.logs},\n"
            f"  batch: {self.batch}\n"
            f")"
        )
    
    @staticmethod
    def from_json(path="pipeline_config.json",name=None):
        """
        Creates a Config objet readin from a json file
        if no file name is provided reads from current folder pipeline_config.json
        this file should have the format
        "name":"pipeline_name", must match the argument pass throug de command line
        "description":"Use this to provide a brefie description of the pipeline",
        "source":"SOURCE/PATH",
        "filters":{
            "dates":["begin date","end date"], time format YYYY-MM-DD
            "region":{
                "asset":"path/to/asset",
                "column":"value",
                "unificar":"Boolean"
            }
        },
        "drop":["colmn1,colmn2,colmn1"],
        "map":{
            "column1":"column1",
            "column2":"column2",
            ...
            }
        "index":"",
        "target":"",
        "logs":"file_name",
        "batch":{ If the data is to large it can be devided in batches by time or subregion
            "lote":"Boolean",
            "time":{
                "year":"1",
                "month":"0",
                "day":"0"
            },
            "subregion":"Boolean"
        }
        """
        with open(path,'r') as file:
            config_list = json.load(file)

        for item in config_list:
            if name == item["name"]:            
                return Configuration(item)
            
    def calculate_dates(self,dates):
        date_format = "%Y-%m-%d"
        for key in dates:
            if dates[key] == "last":
                first_day = datetime.strptime(f"{datetime.now().date().year}-01-01",date_format)
                current_day = datetime.strptime(f"{datetime.now().date()}",date_format)
                delta = first_day-current_day
                days = abs(delta.days)
                last = ((days)-((days)%self.source["refresh_period"]))

                last_entry = first_day + relativedelta(days=last)

                dates[key] = f"{last_entry.date()}"
            elif dates[key] == "":
                dates[key] = None
        return dates