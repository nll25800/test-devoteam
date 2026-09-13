from pydantic import BaseModel
from typing import Literal

#Le shema d'entré ca correspond a la forme d'entre du fichier rapport.json 
class Entry(BaseModel): 
    timestamp: str
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    disk_usage: float
    network_in_kbps: float
    network_out_kbps: float
    io_wait: int
    thread_count: int
    active_connections: int
    error_rate:float
    uptime_seconds: int
    temperature_celsius: float
    power_consumption_watts: float
    service_status: dict[str,str]


#shemas  de sorties ca correspond au format de sortie attendu 
#Une classe Pydantic par clé du fichier Json de sortir : 

class Insights(BaseModel):
    average_latency_ms: float 
    max_cpu_usage: float
    max_memory_usage: float
    error_rate:float
    uptime_seconds: int
    
class Anomaly(BaseModel):
    metric : str
    value :  float
    threshold : float
    severity: Literal["low", "medium", "high"] # selon le pdf cette variable pourra prendre que les trois valeurs
    description : str
    
class Recommendation(BaseModel): 
    id : str
    action : str
    target : str
    parameters :dict
    benefit_estimate :str

class ServiceStatusSummary(BaseModel): 
    online: list[str]
    degraded:list[str]
    offline: list[str]

#Maintenant une classe pour le output.json qui rgroupe toute les clés json

class OutputReport(BaseModel):
    timestamp : str
    insights : Insights
    anomalies : list[Anomaly]
    recommendations : list[Recommendation]
    service_status_summary : ServiceStatusSummary
    

    
    
    
