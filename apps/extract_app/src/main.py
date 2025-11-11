import argparse
import sys
import re
import configparser
import json

from pipeline import *
from connectors import *
from typing import Optional
from models.dengue_model import *
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

def expand_range(estado:str,municipios: str) -> list[str]:
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", municipios)
    if not m:
        raise ValueError("El rango debe tener la forma 'inicio-fin' con dígitos, p. ej. '015-050'")
    start_s, end_s = m.group(1), m.group(2)
    width = max(len(start_s), len(end_s))
    start, end = int(start_s), int(end_s)
    if start > end:
        raise ValueError("El inicio debe ser menor o igual que el fin")
    return [f"'{estado}{str(i).zfill(width)}'" for i in range(start, end + 1)]

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
            args.ini = "../docs/credentials.ini"
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

def predictions_command(args):
    try:
        config = load_config_json(args.config,args.model)
        con_config = load_config_ini(config.get("ini"),config.get("connection"))

        conn = getConnection(con_config)
        conn.test_connection()
        regiones = expand_range(config.get("features_data_Set").get("regiones").get("estado"),
                               config.get("features_data_Set").get("regiones").get("municipios"))

        data_features = conn.get_data(
            config.get("features_data_Set").get("table"),
            config.get("features_data_Set").get("schema"),
            regiones,
            config.get("features_data_Set").get("fechas")
        )

        data_features = data_features.pivot(
                index=['id_region','fecha_inicial','fecha_final','anio','mes'],
                columns='id_tipo',
                values='medicion'
        )

        data_target = conn.get_data(
            config.get("target_data_set").get("table"),
            config.get("target_data_set").get("schema"),
            regiones,
            config.get("target_data_set").get("fechas")
        )

        df_filtered = data_target.merge(data_features, on=['anio','mes'],how='inner')

        df_train,df_test = prepare_features(
            df_filtered,
            target_col= 'casos',
            municipality_col = 'id_region',
            date_col= 'fin_de_mes',
            climate_cols= ['dayl','prcp','srad','tmax','tmin','swe','vp','ndvi'],
            create_time_features = True,
            lags=(1,2,3),
            rolling_windows=(3,7)
        )

        model_path = f"{config.get('path')}{config.get('name')}.ckpt"

        model = load_model(model_path)

        predictions = tft_predict(
            model= model, 
            df=df_test,
            target_col = 'casos',
            municipality_col = 'id_region',
            date_col = 'fin_de_mes',
            max_prediction_length =29,
            batch_size = 64
        )

        monthly_averages = (
            predictions.assign(
                year=lambda x: pd.to_datetime(x['date']).dt.year,
                month=lambda x: pd.to_datetime(x['date']).dt.month
            )
            .groupby(['id_region', 'year', 'month'])
            ['predicted_casos']
            .agg(['mean', 'count', 'std'])
            .round(2)
            .reset_index()
        )

        # Add a formatted date column and sort
        monthly_averages['date'] = pd.to_datetime(monthly_averages[['year', 'month']].assign(day=1))
        monthly_averages = monthly_averages.sort_values(['id_region', 'date'])

        if args.inline:
            print(monthly_averages)
        load_predictions(monthly_averages,conn.get_connection(),modelo=config.get("id"),schema=config.get("features_data_Set").get("schema"),table="predicciones")
    except Exception as e:
        print(e)

def train_model(args):
    try:
        config = load_config_json(args.config,args.model)
        con_config = load_config_ini(config.get("ini"),config.get("connection"))

        conn = getConnection(con_config)
        conn.test_connection()
        regiones = expand_range(config.get("features_data_Set").get("regiones").get("estado"),
                               config.get("features_data_Set").get("regiones").get("municipios"))
        
        # print(config.get("features_data_Set").get("fechas").keys())

        data_features = conn.get_data(
            config.get("features_data_Set").get("table"),
            config.get("features_data_Set").get("schema"),
            regiones,
            config.get("features_data_Set").get("fechas")
        )

        data_features = data_features.pivot(
                index=['id_region','fecha_inicial','fecha_final','anio','mes'],
                columns='id_tipo',
                values='medicion'
        )

        data_target = conn.get_data(
            config.get("target_data_set").get("table"),
            config.get("target_data_set").get("schema"),
            regiones,
            config.get("target_data_set").get("fechas")
        )

        df_filtered = data_target.merge(data_features, on=['anio','mes'],how='inner')

        df_train,df_test = prepare_features(
            df_filtered,
            target_col= 'casos',
            municipality_col = 'id_region',
            date_col= 'fin_de_mes',
            climate_cols= ['dayl','prcp','srad','tmax','tmin','swe','vp','ndvi'],
            create_time_features = True,
            lags=(1,2,3),
            rolling_windows=(3,7)
        )

        df_train = df_train.sort_values(['id_region', 'fin_de_mes'])
        df_test = df_test.sort_values(['id_region', 'fin_de_mes'])

        ### Train model

        model = tft_train_model(  
            df_prepared=df_train,
            target_col = 'casos',
            municipality_col = 'id_region',
            date_col = 'fin_de_mes',
            climate_cols = None,
            max_encoder_length = 30,
            max_prediction_length = 7,
            max_epochs = 5,
            batch_size = 64,
            learning_rate = 0.03,
            random_state = 42,
            device = None,
            path= config.get('path'),
            name= config.get('name')
        )

        # if args.test:

        # if args.inline:
        #     print(predictions)
        # load_predictions(predictions)
    except Exception as e:
        print(e)

def models_command(args):

    try:
        if not args.ini:
            args.ini = "../docs/credentials.ini"
            config = load_config_ini(args.ini,args.con)
            con = getConnection(config)
        match con:
            case PostgresConnector():
                # con.test_connection()
                con.configure({"table": "dim_modelo", "schema": "analytics"})
                lst  = con.get_connection().execute(text("SELECT id_modelo, nombre_modelo, descripcion, fecha_creacion, version FROM analytics.dim_modelo")).fetchall()
                print(" id_modelo - modelo - descripcion - fecha_creacion - version")
                for l in lst:
                    print(f"{l[0]} - {l[1]} - {l[2]} - {l[3]} - {l[4]}")
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
    logs_parser.add_argument("--options", nargs="+",required=False,help="Opciones de lectura de logs")
    logs_parser.set_defaults(func=logs_command)
    
    # DEBUG
    debug_parser = subparsers.add_parser("debug", help="Prueba la conexion a la base de datos y a la API")
    debug_parser.add_argument("--ini", required=False, help="Direccion del archivo .ini a utilizar, si no se especifica un archivo credentials.ini es utilizado")
    debug_parser.add_argument("--con", required=False, help="Nombre de la conexion como se especifica en el archivo .ini")
    debug_parser.set_defaults(func=debug_command)


    # TRAIN MODEL
    train_parser = subparsers.add_parser("train", help="Entrenar un modelo")
    train_parser.add_argument("--config", required=True, help="El archivo .json en el que se establece la configuracion del modelo")
    train_parser.add_argument("--model", required=True, help="Nombre del modelo como se especifica en el archivo .json")
    train_parser.set_defaults(func=train_model)

    # PREDICT
    predict_parser = subparsers.add_parser("predict", help="Realizar predicciones con un modelo entrenado")
    predict_parser.add_argument("--config", required=True, help="El archivo .json en el que se establece la configuracion del modelo")
    predict_parser.add_argument("--model", required=True, help="Nombre del modelo como se especifica en el archivo .json")
    predict_parser.add_argument("--inline", action="store_true",required=False, help="Muestra los resultados en la terminal")
    predict_parser.set_defaults(func=predictions_command)
 

    # MODELOS
    models_parser = subparsers.add_parser("models", help="Regresa informacion sobre los modelos disponibles")
    models_parser.add_argument("--ini", required=False, help="Direccion del archivo .ini a utilizar, si no se especifica un archivo credentials.ini es utilizado")
    models_parser.add_argument("--con", required=True, help="Nombre de la conexion como se especifica en el archivo .ini")
    models_parser.set_defaults(func=models_command)
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
