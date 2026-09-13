from typing import TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

from ingestion import read_json_file
from models import (
    Entry,
    Insights,
    Anomaly,
    Recommendation,
    ServiceStatusSummary,
    OutputReport,
)
from analysis import (
    insights_calcul,
    anomalies_detect,
    service_status_summary_calcul,
)
from recommendation import generate_recommendations


# ---------------------------------------------------------------------------
# État global du pipeline
# ---------------------------------------------------------------------------
# Cet objet représente toutes les informations qui vont circuler
# d'un nœud à l'autre dans notre graphe LangGraph.
#
# L'idée est simple :
# - on commence avec le chemin du fichier contenant les logs ;
# - chaque étape du pipeline enrichit progressivement l'état ;
# - à la fin, on dispose de toutes les informations nécessaires
#   pour générer le rapport final.
class PipelineState(TypedDict):
    logs: list[Entry]
    insights: Insights | None
    anomalies: list[Anomaly]
    recommendations: list[Recommendation]
    status_summary: ServiceStatusSummary | None
    input_path: str
    output_path: str


# ---------------------------------------------------------------------------
# Étape 1 : ingestion des données
# ---------------------------------------------------------------------------
# Cette première étape est volontairement simple :
# elle se contente de lire le fichier JSON et de transformer son contenu
# en objets Entry utilisables par le reste du pipeline.
def ingestion_node(state: PipelineState) -> PipelineState:
    print("📥 Ingestion : chargement des logs...")

    # On récupère le chemin du fichier depuis l'état partagé.
    # Les logs chargés sont ensuite stockés dans state["logs"] pour
    # que les étapes suivantes puissent les utiliser.
    state["logs"] = read_json_file(Entry, state["input_path"])

    print(f"   → {len(state['logs'])} logs chargés.")

    return state


# ---------------------------------------------------------------------------
# Étape 2 : analyse des logs
# ---------------------------------------------------------------------------
# Une fois les logs disponibles, on peut lancer les différents traitements
# d'analyse.
#
# Ici, trois choses sont calculées :
# - les insights généraux sur les données ;
# - les éventuelles anomalies ;
# - un résumé de l'état des services.
#
# Les trois résultats sont ajoutés au même état partagé.
def analysis_node(state: PipelineState) -> PipelineState:
    print("🔎 Analyse : traitement des logs...")

    # Calcul des statistiques et informations générales
    state["insights"] = insights_calcul(state["logs"])

    # Détection des comportements ou valeurs considérés comme anormaux
    state["anomalies"] = anomalies_detect(state["logs"])

    # Création d'un résumé de l'état des différents services
    state["status_summary"] = service_status_summary_calcul(state["logs"])

    print(f"   → {len(state['anomalies'])} anomalies détectées.")

    return state


# ---------------------------------------------------------------------------
# Étape 3 : génération des recommandations
# ---------------------------------------------------------------------------
# Cette étape intervient après l'analyse.
# On transmet uniquement les anomalies au module de recommandation,
# qui va s'appuyer sur le LLM pour proposer des actions ou pistes
# d'amélioration pertinentes.
def recommendation_node(state: PipelineState) -> PipelineState:
    print("💡 Recommandations : génération des recommandations...")

    # Les recommandations sont basées sur les anomalies détectées
    # lors de l'étape précédente.
    state["recommendations"] = generate_recommendations(
        state["anomalies"]
    )

    print(
        f"   → {len(state['recommendations'])} recommandations générées."
    )

    return state


# ---------------------------------------------------------------------------
# Étape 4 : génération du rapport final
# ---------------------------------------------------------------------------
# Cette dernière étape rassemble tous les résultats obtenus jusque-là
# dans un objet OutputReport, puis l'enregistre au format JSON.
def output_node(state: PipelineState) -> PipelineState:
    print("📄 Sortie : génération du rapport final...")

    # On crée un timestamp au format UTC afin de savoir précisément
    # quand le rapport a été généré.
    report = OutputReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        insights=state["insights"],
        anomalies=state["anomalies"],
        recommendations=state["recommendations"],
        service_status_summary=state["status_summary"],
    )

    # Écriture du rapport dans le fichier de sortie.
    # L'encodage UTF-8 permet notamment de conserver correctement
    # les accents et autres caractères spéciaux.
    with open(state["output_path"], "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    print(f"   → Rapport généré : {state['output_path']}")
    print(
        f"   → {len(state['anomalies'])} anomalies détectées, "
        f"{len(state['recommendations'])} recommandations générées."
    )

    return state


# ---------------------------------------------------------------------------
# Construction du graphe LangGraph
# ---------------------------------------------------------------------------
# On définit ici le chemin que vont suivre les données.
#
# Le pipeline est volontairement linéaire :
#
#     ingestion
#         ↓
#      analysis
#         ↓
#   recommendation
#         ↓
#       output
#         ↓
#       END
#
# Chaque nœud reçoit le même état partagé et le met à jour.
def build_graph():
    graph = StateGraph(PipelineState)

    # Déclaration des différentes étapes du pipeline.
    graph.add_node("ingestion", ingestion_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("output", output_node)

    # Le pipeline commence par l'ingestion des données.
    graph.set_entry_point("ingestion")

    # Définition de l'ordre d'exécution des différentes étapes.
    graph.add_edge("ingestion", "analysis")
    graph.add_edge("analysis", "recommendation")
    graph.add_edge("recommendation", "output")

    # Une fois le rapport généré, le workflow est terminé.
    graph.add_edge("output", END)

    # Compilation du graphe pour pouvoir ensuite l'exécuter.
    return graph.compile()


# ---------------------------------------------------------------------------
# Point d'entrée du programme
# ---------------------------------------------------------------------------
# Cette partie n'est exécutée que lorsque le fichier Python est lancé
# directement. Elle permet donc de construire le graphe et de démarrer
# le pipeline avec un état initial.
if __name__ == "__main__":
    # Construction du workflow LangGraph.
    app = build_graph()

    # État de départ du pipeline.
    # Les listes sont initialisées vides et les résultats d'analyse
    # sont encore à None puisqu'ils seront remplis progressivement
    # par les différents nœuds.
    initial_state: PipelineState = {
        "logs": [],
        "insights": None,
        "anomalies": [],
        "recommendations": [],
        "status_summary": None,
        "input_path": "rapport.json",
        "output_path": "output.json",
    }

    # Lancement du pipeline.
    # LangGraph va automatiquement exécuter les nœuds dans l'ordre
    # défini précédemment.
    app.invoke(initial_state)