def print_blocks(file,run_date = "", from_date = "", region = "",message = None):
    with open(file, 'r', encoding='utf-8') as file:
        writing_block = False
        valid_block = False
        block = ''
        for line in file:
            if "Inicia" in line:
                if line.startswith(run_date) and from_date in line and region in line:
                    writing_block = True
                
            if writing_block:
                block += line

            if message and message in line:
                valid_block = True

            if "- Termina -" in line and writing_block:
                writing_block = False

                if (message != '') == valid_block:
                    print(block)
                    block = ''
        
class LogsReader:
    def __init__():
        pass

    @staticmethod
    def read_log(file,**kwargs):

        if not kwargs:
            with open(file, 'r', encoding='utf-8') as file:
                for line in file:
                    print(line.strip())
            return
        
        run_date = kwargs['run_date'] if "run_date" in kwargs.keys() else ""
        from_date = f"desde:{kwargs['from_date']}" if "from_date" in kwargs.keys() else ""
        region = kwargs['region'] if "region" in kwargs.keys() else ""
        message = kwargs['message'] if "message" in kwargs.keys() else ""

        print_blocks(file,run_date=run_date,from_date=from_date,region=region,message=message)