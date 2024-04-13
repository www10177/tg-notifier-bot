import logging

def isTrue(obj: object) -> bool:
    if isinstance(obj,bool):
        return obj
    elif isinstance(obj,str):
        if obj.isnumeric() :
            # Number: 1/0
            return obj.strip() == '1'
        else :
            #Stirng: True, true, 
            return obj.strip().lower() == 'true'
    elif isinstance(obj,int):
        return obj == 1
    else :
        logging.warning(f"Unknown Object Parsed : {obj}")
        return False
    