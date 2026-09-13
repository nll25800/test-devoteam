from models import Entry,Insights,Anomaly


def insights_calcul(log : list[Entry]) -> Insights:
    """Calcule les insights pour le rapport de sortie (output report)
    basé sur l'ensemble des 500 logs d'entrée.
    """
    average_latency_ms = sum(i.latency_ms for i in log)/len(log)  #la moyenne de la lattence 
    max_cpu_usage = max(i.cpu_usage for i in log) # le max de l'usage CPU
    max_memory_usage =max(i.memory_usage for i in log) #Le max l'usage de la mémoire
    error_rate= sum(i.error_rate for i in log)/len(log) #La moyenne de l'erreur
    uptime_seconds = log[-1].uptime_seconds #Recuprer l'uptime le plus recent car il fait qu'augmenter
    
    return Insights( average_latency_ms=average_latency_ms,max_cpu_usage=max_cpu_usage,max_memory_usage=max_memory_usage,error_rate=error_rate,uptime_seconds=uptime_seconds
    )
    
    
    
def check_anomaly(metric_name, value, low_th, med_th, high_th, unit=""):
    """ Verifier si une valeur dépasse le seuil minimal d'anomalie et retourne l'objet Anomaly associé.  """

    if value <= low_th: 
       return None
    severity = "high" if value > high_th else "medium" if value > med_th else "low"
    return Anomaly( 
               metric=metric_name, value=value, threshold=low_th,
               severity = severity,
               description =f"Pic de {metric_name} détecté à {value}{unit}, dépassant le seuil de {low_th}{unit}."
                  )

""" Defénition des seuils d'alerte pour chaque métrique
    CPU_th : Pourcentage CPU maximal toléré
    MEMORY_th : Pourcentage Memoire maximal toléré
    Latence_th : Latence maximale tolérée
    error_rate_th : taux d'erreur maximal toléré """
    
def anomalies_detect(logs : list[Entry],CPU_th= 80,MEMORY_th= 85,Latence_th= 200,error_rate_th= 0.05) -> list [Anomaly] : 
    """ Pour chaque ametrique (memoire,CPU,latence et erreur rate) anomlies_detect
    identifie la valeur maximale atteinte et genere une anomali si le seuil est dépassé """
    
    anomalies = []
    #Analyse du CPU : 
    CPU_MAX_value= max(i.cpu_usage for i in logs)
    anomalies.append(check_anomaly("cpu_usage",CPU_MAX_value,CPU_th,85,90,unit="%"))
        
    #analyse de la mémoire : 
    memory_max_value= max(i.memory_usage for i in logs)
    anomalies.append(check_anomaly("memory_usage",memory_max_value,MEMORY_th,88,93,unit="%"))
                
        
    #analyse de la latence : 
    Latence_max_value= max(i.latency_ms for i in logs)
    anomalies.append(check_anomaly("Latency_ms",Latence_max_value,Latence_th,250,300,unit="ms"))
    
            
    #analyse du taux d'erreur: 
    error_max_value= max(i.error_rate for i in logs)
    anomalies.append(check_anomaly("error_rate",error_max_value,error_rate_th,0.07,0.1,unit=" "))
    
    return[a for a in anomalies if a is not None]
                            
        
from models import Entry, ServiceStatusSummary


def service_status_summary_calcul(logs: list[Entry]) -> ServiceStatusSummary:
    """Regroupe les services par statut, basé sur la dernière entrée de logs."""
    if not logs:
        return ServiceStatusSummary(online=[], degraded=[], offline=[])

    status_map = logs[-1].service_status

    return ServiceStatusSummary(
        online=[
            service
            for service, status in status_map.items()
            if status == "online"
        ],
        degraded=[
            service
            for service, status in status_map.items()
            if status == "degraded"
        ],
        offline=[
            service
            for service, status in status_map.items()
            if status == "offline"
        ],
    )

