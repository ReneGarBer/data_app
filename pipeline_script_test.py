"""
1.- Sigue arreglar las siguientes opciones del menú.
2.- Implementar el pipeline para cargar a la base de datos.
"""
import sys
import re
import configparser
from configuration import Configuration as config

from pipeline import EEpipelines

# Verifica que se haya proporcionado al menos un argumento
if len(sys.argv) > 1:
    arg = sys.argv[1]  # Toma el primer argumento
    
    match arg:
        case _ if re.fullmatch(r'(-h|help)', arg):  # Patrón para -h o --help
            #imprimir en consola mensaje de ayuda
            print("help")
        case _ if re.fullmatch(r'(-r|run)', arg):  # Patrón para -r o --run
            #leer archivo json
            config = config.from_json(path=sys.argv[3],name=sys.argv[2])

            credentials = configparser.ConfigParser()
            credentials.read("credentials.ini")
            credentials = dict(credentials['eeAPI'])
            #print(config)
            #print(credentials)
            eepipeline = EEpipelines(config,credentials)

            eepipeline.run_pipeline_csv()
            
        case _ if re.fullmatch(r'(-l|logs)', arg):  # Patrón para -l o --logs
            print("logs")
        case _:
            print("error")
else:
    print("No argument given")
