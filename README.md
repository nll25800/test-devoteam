# Optimisation de l'Infrastructure Technique

Application permettant d'analyser des logs d'infrastructure, de détecter des anomalies de performance et de générer des recommandations d'optimisation.

## Objectif

L'application génère un rapport structuré (`output.json`) contenant :

- des indicateurs de performance (`insights`) ;
- les anomalies détectées à partir de seuils définis ;
- des recommandations d'actions correctives générées par un LLM ;
- un résumé de l'état des différents services.

## Architecture

Le traitement est organisé sous forme d'un pipeline composé de plusieurs nœuds, qui s'enchaînent dans l'ordre suivant :

```text
rapport.json
     |
     v
[ ingestion ]        Lecture et validation des logs
     |
     v
[ analysis ]         Calcul des insights + détection des anomalies
     |
     v
[ recommendation ]   Génération des recommandations via LLM
     |
     v
[ output ]           Écriture du rapport final (output.json)
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

LangGraph permet de représenter clairement le pipeline sous forme de nœuds successifs, avec un état partagé qui circule entre eux.

Le choix d'un graphe permet également de faire évoluer plus facilement le pipeline par la suite, par exemple en ajoutant une étape de validation, un nouveau traitement, ou une branche conditionnelle (par exemple, un traitement prioritaire si une anomalie de sévérité "high" est détectée).

### LLM

Le LLM est utilisé uniquement pour générer les recommandations dans `recommendation.py`.

La détection des anomalies et le calcul des indicateurs restent déterministes (basés sur des seuils numériques). Cela permet de garder une analyse reproductible et rapide, et de réserver l'utilisation du LLM à la tâche où il apporte une réelle valeur ajoutée : la formulation d'une recommandation contextualisée en langage naturel.

Le projet utilise **Groq** avec le modèle `openai/gpt-oss-120b`. Le prompt système impose explicitement une réponse en français et un format JSON strict, afin de garantir la cohérence linguistique et structurelle du rapport final.

## Détection des anomalies

Les données fournies dans le sujet ne définissent pas de seuils précis pour les anomalies ("une utilisation excessive du CPU, une latence élevée, etc."). Les seuils suivants ont donc été définis à partir de deux sources complémentaires :

1. **Pratiques usuelles de supervision d'infrastructure** : des seuils communément admis en observabilité, indépendants du jeu de données fourni.
2. **Observation empirique du jeu de données fourni** (`rapport.json`) : les seuils ont été calibrés pour bien séparer le fonctionnement normal des pics anormaux réellement observés dans les 500 entrées de logs (par exemple, un CPU habituellement autour de 55-60 %, avec des pics isolés à 93-99 % coïncidant avec un passage du service `api_gateway` en statut `degraded`).

| Métrique | Seuil | Sévérité medium | Sévérité high |
|---|---:|---:|---:|
| CPU | 80 % | 85 % | 90 % |
| Mémoire | 85 % | 88 % | 93 % |
| Latence | 200 ms | 250 ms | 300 ms |
| Taux d'erreur | 0.05 | 0.07 | 0.10 |

Le passage en sévérité `medium` puis `high` permet de distinguer un dépassement léger d'une situation réellement critique, plutôt qu'un simple indicateur binaire anomalie / pas anomalie.

Ces seuils restent des constantes fixes dans le code, choisies pour ce jeu de données précis. Dans un contexte de production réel, ils gagneraient à être externalisés dans un fichier de configuration, voire calculés dynamiquement par rapport à une baseline historique.

## Statut des services

Le champ `service_status_summary` fournit un état des services réparti entre :

- `online`
- `degraded`
- `offline`

Le statut utilisé correspond à la dernière entrée disponible dans les logs. Le résultat représente donc un **snapshot de l'état actuel** des services plutôt qu'un historique complet sur la période.

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
GROQ_API_KEY=votre_cle_api
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
- ajouter une gestion plus complète des erreurs (retry sur l'appel LLM, logging structuré) ;
- enrichir les règles de détection avec des données historiques ou une baseline dynamique ;
- ajouter d'autres nœuds au pipeline, par exemple une étape de validation ou de priorisation des anomalies, éventuellement via une branche conditionnelle LangGraph selon la sévérité globale du rapport.

Ces évolutions pourraient être ajoutées sans modifier le principe général du pipeline.