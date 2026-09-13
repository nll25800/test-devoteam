import os 
import json
from dotenv import load_dotenv
from groq import Groq
from models import Anomaly, Recommendation
from uuid import uuid4

# Chargement des variables d'environnement
load_dotenv()
# Initialisation du client Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL="openai/gpt-oss-120b"
SYSTEM_PROMPT = """Tu es un expert en infrastructure système et cloud.
Ton role est de générer une recommandation technique pour résoudre l'anomalie fournie.

Tu dois répondre strictement au format JSON valide avec les clés suivantes  : {"action": "string", "target": "string", "parameters": {}, "benefit_estimate": "string"}"""

def generate_single_recommandation(anomaly : Anomaly) -> dict: 
    """ Génère une recommandation brute sous forme de dictionnaire via l'API Groq

    pour une anomalie donnée.
    """
    user_prompt= (
        f"Anomalie détectée :\n"
        f"- métrique : {anomaly.metric}\n"
        f"-valeur observée :{anomaly.value}\n"
        f"- seuil défini : {anomaly.threshold}\n"
        f"-sévérité : {anomaly.severity}\n"
        f"-decription du problème : {anomaly.description}"   
    ) 
    response = client.chat.completions.create ( 
        model = MODEL,
        response_format={"type": "json_object"}, # Forcer la réponse au format JSON
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT },
            {"role": "user", "content": user_prompt },
                  ],
     )
    return json.loads(response.choices[0].message.content)
    

def generate_recommendations(anomalies: list[Anomaly]) -> list[Recommendation] : 
    """Parcourt une liste d'anomalies, génère leurs recommandations

    et les transforme en objets Pydantic Recommendation.
    """
    recommandations_list : list[Recommendation] = []
    for a in anomalies: 
        item =generate_single_recommandation(a)
        if item: 
            if isinstance(item,dict) and "id" not in item : 
                item["id"] = str(uuid4()) #ca permet de générer un ID pour chaque recommendation
            recommandations_list.append(Recommendation.model_validate(item) ) # Validation Pydantic et instanciation de l'objet
        
    return recommandations_list
    

