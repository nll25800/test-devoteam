import json 
from models import Entry

def read_json_file(cls,nameFile) -> list[cls]: 
    """lire le fichier rapport.json et le transfomer en liste d'objets (class entry ) """
    with open(nameFile, 'r',encoding='utf-8') as file:
     data = json.load(file)
    return [cls(**bloc) for bloc in data]


