# Optimisation de l'Infrastructure Technique

Application permettant d'analyser des logs d'infrastructure, de détecter des anomalies de performance et de générer des recommandations d'optimisation.

## Objectif

L'application génère un rapport structuré (`output.json`) contenant :

- des indicateurs de performance (`insights`) ;
- les anomalies détectées à partir de seuils définis ;
- des recommandations d'actions correctives générées par un LLM ;
- un résumé de l'état des différents services.

## Architecture

Le traitement est organisé sous forme d'un pipeline composé de plusieurs nœuds :

```text
rapport.json
     │
     ▼
┌──────────────┐
│  ingestion   │
│              │
│ Lecture et   │
│ validation   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   analysis   │
│              │
│ Insights +   │
│ anomalies    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ recommendation   │
│                  │
│ Recommandations  │
│ générées par LLM │
└────────┬─────────┘
         │
         ▼
┌──────────────┐
│    output    │
│              │
│ Génération   │
│ du rapport   │
└──────────────┘
```

L'orchestration de ces étapes est réalisée avec **LangGraph**. Chaque étape reçoit et met à jour un état partagé (`PipelineState`).

## Structure du projet

| Fichier | Rôle |
|---|---|
| `models.py` | Définit les modèles de données d'entrée et de sortie avec Pydantic |
| `ingestion.py` | Charge et valide les données du fichier `rapport.json` |
| `analysis.py` | Calcule les indicateurs, détecte les anomalies et analyse le statut des services |
| `recommendation.py` | Génère les recommandations à partir des anomalies détectées |
| `main.py` | Construit et exécute le pipeline LangGraph |
| `rapport.json` | Fichier contenant les logs d'entrée |
| `output.json` | Rapport final généré par l'application |

## Choix techniques

### Python

Python a été choisi pour sa simplicité et pour disposer facilement de bibliothèques adaptées au traitement de données et à l'intégration de LLM.

### Pydantic

Pydantic est utilisé pour définir les structures des données d'entrée et de sortie.

Cela permet notamment de :

- valider les données des logs avant leur traitement ;
- manipuler des objets typés dans le pipeline ;
- garantir une structure cohérente pour le rapport final.

### LangGraph

LangGraph permet de représenter clairement le pipeline sous forme de nœuds successifs.

Le choix d'un graphe permet également de faire évoluer plus facilement le pipeline par la suite, par exemple en ajoutant une étape de validation ou un nouveau traitement.

### LLM

Le LLM est utilisé uniquement pour générer les recommandations dans `recommendation.py`.

La détection des anomalies et le calcul des indicateurs restent déterministes. Cela permet de garder une analyse reproductible et de réserver l'utilisation du LLM à la génération de recommandations.

Le projet utilise actuellement **Groq** avec le modèle `openai/gpt-oss-120b`.

## Détection des anomalies

Les données fournies dans le sujet ne définissent pas de seuils précis pour les anomalies. Des seuils ont donc été définis pour les principales métriques :

| Métrique | Seuil | Sévérité medium | Sévérité high |
|---|---:|---:|---:|
| CPU | 80 % | 85 % | 90 % |
| Mémoire | 85 % | 88 % | 93 % |
| Latence | 200 ms | 250 ms | 300 ms |
| Taux d'erreur | 0.05 | 0.07 | 0.10 |

Ces valeurs sont utilisées comme règles de détection simples et explicables. Elles pourraient être externalisées dans une configuration dédiée dans une version destinée à la production.

## Statut des services

Le champ `service_status_summary` fournit un état des services réparti entre :

- `online`
- `degraded`
- `offline`

Le statut utilisé correspond à la dernière entrée disponible dans les logs. Le résultat représente donc un **snapshot de l'état actuel** des services plutôt qu'un historique.

## Installation

Créer un environnement virtuel :

```bash
python3 -m venv venv
```

Activer l'environnement virtuel.

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer ensuite un fichier `.env` à la racine du projet :

```env
GROQ_API_KEY=votre_clé_api
```

## Exécution

Lancer le pipeline avec :

```bash
python main.py
```

Le fichier `rapport.json` est utilisé comme entrée et le rapport final est généré dans :

```text
output.json
```

## Format du résultat

Le rapport généré contient les principales informations suivantes :

```json
{
  "timestamp": "...",
  "insights": {
    "average_latency_ms": 0,
    "max_cpu_usage": 0,
    "max_memory_usage": 0,
    "error_rate": 0,
    "uptime_seconds": 0
  },
  "anomalies": [],
  "recommendations": [],
  "service_status_summary": {
    "online": [],
    "degraded": [],
    "offline": []
  }
}
```

Le format de sortie est défini par les modèles Pydantic du projet afin de rester conforme au schéma demandé dans le test technique.

## Limites et évolutions possibles

Quelques améliorations pourraient être apportées dans une version plus avancée :

- ajouter des tests unitaires et d'intégration ;
- externaliser les seuils de détection dans un fichier de configuration ;
- ajouter une gestion plus complète des erreurs d'entrée ;
- enrichir les règles de détection avec des données historiques ;
- ajouter d'autres nœuds au pipeline, par exemple une étape de validation ou de priorisation des anomalies.

Ces évolutions pourraient être ajoutées sans modifier le principe général du pipeline.