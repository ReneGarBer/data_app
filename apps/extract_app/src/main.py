import argparse
import sys
from pipeline import *
import configparser
from connectores import *
from typing import Optional
import json
from logs_reader import LogsReader

def valid_logs_options(keys):
    valid_keys = {"region", "run_date", "from_date", "message"}

    for key in keys:
        if key not in valid_keys:
            return False
    return True

def load_config_json(file: str, section: str) -> dict:
    with open(file, 'r') as f:
        config = json.load(f)
    
    for data in config:
        if data['name'] == section:
            return data  
    raise ValueError(f"Sección '{section}' no encontrada en {file}")

def load_config_ini(file, section):
    config = configparser.ConfigParser()
    config.read(file)
    if section not in config:
        raise ValueError(f"Sección '{section}' no encontrada en {file}")
    return config[section]

def getConnection(config: dict) -> Optional['DBConnector']:
    match config.get("con_type"):
        case "postgresql":
            return PostgresConnector(config)
        case "eeAPI":
            return EEConnector(config)
        case _:
            return None

def run_command(args):
    config = load_config_json(args.config,args.pipeline)

    con_config = load_config_ini(config.get("source").get("ini"),config.get("source").get("con"))
    source_con = getConnection(con_config)
    con_config = load_config_ini(config.get("target").get("ini"),config.get("target").get("con"))
    target_con = getConnection(con_config)

    pipeline = EEpipelines(config,source_con,target_con)
   
    match args.format:
        case "sql":
            pipeline.run_sql()
        case "csv":
            pipeline.run_csv()            

def logs_command(args):
    try:
        config = load_config_json(args.config,args.pipeline)
        file = config.get('logs')

        if args.options:
            args.options = dict(opt.split(":", 1) for opt in args.options)        

            if valid_logs_options(args.options.keys()):
                LogsReader.read_log(file=file,**args.options)
            else:
                print("invalid key")
        else:
            LogsReader.read_log(file=file)
    except Exception as e:
        print(e)


def debug_command(args):
    try:
        if not args.ini:
            args.ini = "docs/credentials.ini"
        config = load_config_ini(args.ini,args.con)
        con = getConnection(config)
        match con:
            case PostgresConnector():
                con.test_connection()
            case EEConnector():        
                con.initialize_connection()
            case _:
                print("Conector no encontrado")
    except Exception as e:
        print(e)

    
def main():
    parser = argparse.ArgumentParser(
        description="Este script es utilizado para extraer datos y cargarlos a la base de datos o a un archivo csv",
        usage='%(prog)s <comando> <formato>'
    )
    
    subparsers = parser.add_subparsers(title="Comandos", dest="command")
    
    # RUN
    run_parser = subparsers.add_parser("run", help="Ejecuta un proceso de ETL (pipeline).")
    run_parser.add_argument("--format", choices=["sql", "csv"],required=True, help="sql: Carga los datos a una base de dato\ncsv: Carga los datos a un archivo .csv")
    run_parser.add_argument("--config", required=True, help="El archivo .json en el que se establece la configuracion del proceso de ETL")
    run_parser.add_argument("--pipeline", required=True, help="Nombre del proceso de ETL")
    run_parser.set_defaults(func=run_command)
    
    # LOGS
    logs_parser = subparsers.add_parser("logs", help="Mostrar los de un proceso de ETL (pipeline)")
    logs_parser.add_argument("--config", required=True, help="El archivo .json en el que se establece la configuracion del proceso de ETL")
    logs_parser.add_argument("--pipeline", required=True, help="Nombre del proceso de ETL")
    #"region", "run_date", "from_date", "message"
    logs_parser.add_argument("--options", nargs="+",required=False,help="Opciones de lectura de logs")
    logs_parser.set_defaults(func=logs_command)
    
    # DEBUG
    debug_parser = subparsers.add_parser("debug", help="Prueba la conexion a la base de datos y a la API")
    debug_parser.add_argument("--ini", required=False, help="Direccion del archivo .ini a utilizar, si no se especifica un archivo credentials.ini es utilizado")
    debug_parser.add_argument("--con", required=True, help="Nombre de la conexion como se especifica en el archivo .ini")
    debug_parser.set_defaults(func=debug_command)

    # HELP (optional, because argparse already provides -h/--help)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
