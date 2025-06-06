import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Configuration:
    def __init__(self,config):
        try:      
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
            self.table = config["table"]
            self.schema = config["schema"]
        except TypeError:
            raise TypeError(f"Configuration.__init__(self, config): config: valor: '{config}', tipo: {type(config)}")

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
    
    @classmethod
    def from_json(cls,path="pipeline_config.json",name=None):
        with open(path,'r') as file:
            config_list = json.load(file)
        for item in config_list:
            if name == item["name"]:            
                return cls(item)
        return cls(f"{name} no fue encontrado en {path}")

    @classmethod     
    def calculate_dates(cls,dates):
        date_format = "%Y-%m-%d"
        for key in dates:
            if dates[key] == "last":
                first_day = datetime.strptime(f"{datetime.now().date().year}-01-01",date_format)
                current_day = datetime.strptime(f"{datetime.now().date()}",date_format)
                delta = first_day-current_day
                days = abs(delta.days)
                last = ((days)-((days)%cls.source["cadence"]))

                last_entry = first_day + relativedelta(days=last)

                dates[key] = f"{last_entry.date()}"
            elif dates[key] == "":
                dates[key] = None
        return dates