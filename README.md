# Optimisation de l'Infrastructure Technique

Application qui lit des logs d'infrastructure (`rapport.json`), détecte des anomalies de performance et génère un rapport structuré (`output.json`) contenant des insights, les anomalies détectées et des recommandations d'optimisation générées par un LLM.

## Architecture

Le pipeline est organisé en 4 étapes qui s'enchaînent :

```
rapport.json
     |
     v
[ ingestion ]        lecture et validation des logs
     |
     v
[ analysis ]         calcul des insights + détection des anomalies
     |
     v
[ recommendation ]   génération des recommandations via LLM
     |
     v
[ output ]           écriture de output.json
```

L'orchestration est réalisée avec **LangGraph** : chaque étape est un nœud qui lit et met à jour un état partagé (`PipelineState`).

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `models.py` | Schémas Pydantic : `Entry` (entrée), `Insights`, `Anomaly`, `Recommendation`, `ServiceStatusSummary`, `OutputReport` (sortie) |
| `ingestion.py` | Charge `rapport.json` et valide chaque entrée via Pydantic |
| `analysis.py` | Calcule les insights de synthèse, détecte les anomalies par seuils, calcule le statut des services |
| `recommendation.py` | Appelle Groq pour générer une recommandation par anomalie détectée |
| `main.py` | Assemble le pipeline LangGraph et écrit `output.json` |

## Choix techniques

- **Python + Pydantic** : validation stricte des données d'entrée et de sortie, garantissant la conformité au schéma attendu.
- **Détection d'anomalies déterministe** (seuils numériques), plutôt que via un LLM : rapide, reproductible, peu coûteux.
- **LLM (Groq, `openai/gpt-oss-120b`) réservé aux recommandations** : c'est la seule étape où la génération en langage naturel apporte une réelle valeur ajoutée. Le prompt impose une réponse en français et un format JSON strict.
- **LangGraph plutôt qu'un enchaînement de fonctions simples** : rend la structuration en nœuds explicite, et permettrait d'ajouter facilement une branche conditionnelle (ex. traitement prioritaire si une anomalie est de sévérité `high`).

## Seuils de détection

Le sujet ne précise pas de seuils exacts. Les valeurs suivantes ont été choisies à partir de pratiques courantes de supervision d'infrastructure, puis vérifiées sur le jeu de données fourni (par exemple, le CPU tourne normalement autour de 55-60 %, avec des pics isolés à 93-99 %, ce qui confirme la pertinence du seuil de 80 %).

| Métrique | Seuil | Sévérité medium | Sévérité high |
|---|---:|---:|---:|
| CPU | 80 % | 85 % | 90 % |
| Mémoire | 85 % | 88 % | 93 % |
| Latence | 200 ms | 250 ms | 300 ms |
| Taux d'erreur | 0.05 | 0.07 | 0.10 |

## Statut des services

`service_status_summary` reflète le statut le plus récent de chaque service (dernière entrée du fichier de logs) — un snapshot de l'état actuel, pas un historique sur toute la période.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
pip install pydantic langgraph groq python-dotenv
```

Créer un fichier `.env` à la racine :
```
GROQ_API_KEY=votre_cle
```

## Exécution

```bash
python main.py
```

Le rapport est généré dans `output.json`.

## Limites connues

- Pas de mécanisme de retry en cas d'échec de l'appel LLM.
- Seuils fixes dans le code plutôt qu'externalisés dans un fichier de configuration.