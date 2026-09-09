# -*- coding: utf-8 -*-
"""Recommandation et assistant conversationnel (Feature 5).

Construit un résumé de contexte à partir des données de l'organisation
(écritures, analyses) puis :
  - appelle le LLM (Gemini) pour une réponse en français si la clé est configurée ;
  - sinon renvoie une réponse locale structurée à partir des statistiques.

Ne lève jamais d'exception : repli dégradé garanti.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

logger = logging.getLogger(__name__)

try:
    from agents.llm import invoke_text
    _HAS_LLM = True
except Exception:  # pragma: no cover
    _HAS_LLM = False

# Timeout bornant l'appel LLM pour ne jamais bloquer l'assistant.
LLM_TIMEOUT_SECONDS = 12


def build_context(org_data: dict) -> str:
    """Transforme les données de l'organisation en cadre lisible pour la réponse."""
    parts = [f"Aperçu de l'organisation « {org_data.get('org_name', '')} » :"]

    entries = org_data.get("entries", [])
    parts.append(f"- {len(entries)} écritures comptables au total.")
    if entries:
        sources = {}
        total = 0.0
        for e in entries:
            sources[e.get("source", "manuel")] = sources.get(e.get("source", "manuel"), 0) + 1
            total += float((e.get("lines") or [{}])[0].get("amount") or 0.0) if e.get("lines") else 0.0
        parts.append(
            "- Répartition par source : "
            + ", ".join(f"{k} {v}" for k, v in sources.items())
            + f". Total {total:,.0f} CDF.".replace(",", " ")
        )

    analyses = org_data.get("analyses", [])
    risk = [a.get("risk_score") for a in analyses if a.get("risk_score") is not None]
    if risk:
        avg = sum(risk) / len(risk)
        parts.append(f"- {len(analyses)} analyses effectuées, score de risque moyen {avg:.1f}/100.")
    else:
        parts.append(f"- {len(analyses)} analyses effectuées.")

    anomalies = org_data.get("anomalies", [])
    if anomalies:
        parts.append(f"- {len(anomalies)} anomalies détectées au total.")
        from collections import Counter
        by_type = Counter(a.get("type", "Autre") for a in anomalies)
        parts.append("  Types les plus fréquents : " + ", ".join(f"{k} ({v})" for k, v in by_type.most_common(5)))

    return "\n".join(parts)


def _local_answer(question: str, org_data: dict) -> str:
    """Réponse locale (sans LLM) sur des questions fréquentes."""
    q = question.lower()
    entries = org_data.get("entries", [])
    analyses = org_data.get("analyses", [])
    anomalies = org_data.get("anomalies", [])

    if any(k in q for k in ("combien", "écriture", "journal", "combien d'")):
        return (f"Votre organisation compte actuellement {len(entries)} écriture(s) comptable(s). "
                f"Réparties par source : "
                + ", ".join(f"{k} ({v})" for k, v in _source_counts(entries).items()))
    if any(k in q for k in ("risque", "score", "analyse")):
        risk = [a.get("risk_score") for a in analyses if a.get("risk_score") is not None]
        avg = (sum(risk) / len(risk)) if risk else 0.0
        return (f"Vous avez réalisé {len(analyses)} analyse(s). "
                f"Le score de risque moyen observé est de {avg:.1f}/100 "
                f"sur {len(anomalies)} anomalie(s) détectée(s).")
    if any(k in q for k in ("anomalie", "alerte", "vue")):
        if not anomalies:
            return "Aucune anomalie détectée pour le moment."
        from collections import Counter
        by_type = Counter(a.get("type", "Autre") for a in anomalies)
        top = ", ".join(f"{k} ({v})" for k, v in by_type.most_common(5))
        return f"Voici les anomalies détectées : {top}. Consultez le rapport pour le détail."
    if any(k in q for k in ("bonjour", "salut", "hello", "aide", "help")):
        return ("Bonjour ! Je suis l'assistant LucidAI. Posez-moi des questions sur vos "
                "analyses, anomalies, écritures ou risques, par exemple : "
                "« combien d'écritures ai-je ? » ou « quel est mon niveau de risque ? ».")

    # Réponse générique locale
    return (f"Voici ce que je vois pour votre organisation : {len(entries)} écriture(s), "
            f"{len(analyses)} analyse(s), {len(anomalies)} anomalie(s). "
            "Pour des réponses plus fines, connectez une clé d'IA (GEMINI_API_KEY) en production.")


def _source_counts(entries: list) -> dict:
    counts = {}
    for e in entries:
        s = e.get("source", "manuel")
        counts[s] = counts.get(s, 0) + 1
    return counts


def answer(question: str, org_data: dict, history: list | None = None) -> dict:
    """Répond à une question. Retourne {text, mode} où mode = 'llm' | 'local'."""
    context = build_context(org_data)
    prompt = (
        "Tu es l'assistant d'audit financier LucidAI, destiné aux PME francophones (RDC). "
        "Réponds en français, de façon concise et claire, en t'appuyant uniquement sur les "
        "données fournies.\n\n"
        f"{context}\n\n"
        "Question de l'utilisateur :\n"
        f"{question}"
    )

    if _HAS_LLM:
        try:
            from config import config
            if config.GEMINI_API_KEY:
                # Appel LLM borné dans le temps. IMPORTANT : on n'utilise PAS
                # `with ThreadPoolExecutor` car son `shutdown(wait=True)` à la
                # sortie bloque jusqu'à la fin réelle de l'appel réseau, ce qui
                # neutralise le timeout. On gère l'executor manuellement avec
                # shutdown(wait=False, cancel_futures=True) pour que le repli
                # local soit immédiat dès le dépassement du délai.
                ex = ThreadPoolExecutor(max_workers=1)
                future = ex.submit(invoke_text, prompt)
                try:
                    text = future.result(timeout=LLM_TIMEOUT_SECONDS)
                    return {"text": text.strip(), "mode": "llm"}
                finally:
                    ex.shutdown(wait=False, cancel_futures=True)
        except FuturesTimeout:  # pragma: no cover
            logger.warning("Assistant: délai LLM dépassé, repli local.")
        except Exception as e:  # pragma: no cover
            logger.warning("Assistant: échec LLM (%s), repli local.", e)

    return {"text": _local_answer(question, org_data), "mode": "local"}
