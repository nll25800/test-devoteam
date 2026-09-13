# Optimisation de l'Infrastructure Technique

Une optimisation qui integre des dlogs serveur, détecte des anomalies de performance et gènere des recommandation d'optimisation.


## Objectif

Génerer un rapport structuré (`output.json`) qui contient  :
- des Inndicateurs (Insights)
- les anomalies détectées (En se basant sur des seuils choisis par le développeur --> des estimations)
- des recommandations d'actions correctives, générées par un LLM
- un état des lieux des services (online / degraded / offline)

## Architecture

Le pipeline est organisé en 3 étapes séquentielles, correspondant chacune à un fichier dédié :

```
rapport.json
     │
     ▼
┌─────────────┐
│ ingestion.py│  Lecture + validation des logs (Pydantic) 
└──────┬──────┘
       ▼
┌─────────────┐
│ analysis.py │  Calcul des insights + détection des anomalies
└──────┬──────┘
       ▼
┌───────────────────┐
│ recommendation.py  │  Génération des recommandations via (Groq)
└──────┬─────────────┘
       ▼
┌─────────────┐
│  main.py    │  Assemblage du rapport final + écriture de output.json en utilisant LangGraph
└─────────────┘
La structure des données d'entré et de sortie est définie dans le script models.py qui utilise la bibliotheque Pydantic
```

### Fichiers du projet

| Fichier | Rôle |
|---|---|
| `models.py` | définir  les entrés (logs) et les sorties de l'applications |
| `ingestion.py` | Charger les données d'entrées  `rapport.json`, les valider en une liste d'objets `Entry` |
| `analysis.py` | Calcule les indicateur (Insights), détecte les anomalies par seuils, calcule le statut des services |
| `recommendation.py` | Pour chaque anomalie,  le LLM (Groq)  génére une recommandation  |
| `main.py` | Point d'entrée : orchestre les 3 étapes et écrit `output.json` |


## Choix techniques

### Validation des données : Pydantic
Chaque donnée manipulée (entrée comme sortie) devrait respecter une structure précise. Cela garantit que :
- les données d'entrée sont bien structurés avant tout traitement 
- le rapport de sortie respecte exactement le schéma JSON attendu (demandé dans le test)

### Orchestration : LangGraph
Le pipeline est orchestré avec LangGraph plutôt qu'un simple enchaînement de fonctions. Chaque étape (ingestion, analyse, recommandation, sortie) est modélisée comme un nœud, avec un état partagé (`PipelineState`) qui transite entre eux. 

### LLM : Groq (modèle `openai/gpt-oss-120b`)
Utilisé uniquement dans `recommendation.py`, pour générer le texte des recommandations à partir des anomalies détectées. 



## Détection d'anomalies
Le sujet ne fournissant aucun seuil précis ("une utilisation excessive du CPU, une latence élevée, etc."), les valeurs suivantes ont été définies à partir des pratiques usuelles de supervision d'infrastructure :

| Métrique | Seuil de déclenchement | Sévérité medium | Sévérité high |
|---|---|---|---|
| CPU usage | 80% | 85% | 90% |
| Memory usage | 85% | 88% | 93% |
| Latence | 200 ms | 250 ms | 300 ms |
| Taux d'erreur | 0.05 | 0.07 | 0.1 |

Ces seuils sont basés sur des pratiques courantes de supervision d'infrastructure, et ajustés en observant la distribution des données du jeu de test fourni.

## Statut des services
`service_status_summary` reflète le **statut le plus récent** de chaque service (dernière entrée du fichier de logs), plutôt qu'un historique des statuts sur toute la période — cohérent avec une vision "snapshot" de l'état actuel de l'infrastructure.



## Installation et exécution

```bash
python3 -m venv venv
venv\Scripts\activate
pip install pydantic groq python-dotenv
```

Créer un fichier `.env` à la racine avec :
```
GROQ_API_KEY=votre_clé_ici
```

Lancer le pipeline complet :
```bash
python main.py
```

Le rapport est généré dans `output.json`.

