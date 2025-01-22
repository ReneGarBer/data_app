import sys
import re
import configparser
from configuration import Configuration
from pipeline import EEpipelines

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 5:
        print("Usage: myscript.py [run [-csv | -sql] 'parameter1' ['filename'] | help | logs 'parameter1' ['filename'] ]")
        return

    command = sys.argv[1].lower()

    if command == "help":
        print("Usage instructions:")
        print("- run -csv 'parameter1' 'filename' to load CSV into the database.")
        print("- run -sql 'parameter1' to run a custom SQL command.")
        print("- logs 'parameter1' 'filename' to perform logging actions.")
    elif command == "run" and len(sys.argv) >= 4:
        option = sys.argv[2].lower()
        name = sys.argv[3]
        config_file = None

        if len(sys.argv) == 5:
            config_file = sys.argv[4]
        try:
            config = Configuration.from_json(path=config_file,name=name)
            credentials = configparser.ConfigParser()
            credentials.read("credentials.ini")
            credentials = {"eeAPI":dict(credentials['eeAPI']), "postgresql":dict(credentials['postgresql'])}
            eepipeline = EEpipelines(config,credentials)
        except Exception as e:
            print(e)

        if option == "-csv":
            eepipeline.run_pipeline_csv()
            # print("Borra esto")
        elif option == "-sql":
            eepipeline.pipeline_to_db()
            # print("Borra esto")
        else:
            print("Invalid run command syntax.")

    elif command == "logs" and len(sys.argv) >= 3:
        parameter1 = sys.argv[2]
        filename = sys.argv[3] if len(sys.argv) > 3 else None
        print(f"Logging with parameter: {parameter1}")
        if filename:
            print(f"Using log file: {filename}")
        # Add logging logic here
    else:
        print("Invalid command or insufficient parameters.")

if __name__ == "__main__":
    main()