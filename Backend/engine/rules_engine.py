import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["amount", "date", "vendor"]
OPTIONAL_COLUMNS = ["tax_rate"]

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Fournisseurs considérés comme non approuvés / à risque (base locale ajustable)
BLACKLISTED_VENDORS = [
    "UNKNOWN VENDOR", "OFFSHORE CORP", "CASH PAYMENT",
    "SHELL HOLDINGS", "SOCIETE FANTOME", "DOSSIER CASH",
]


def _safe_dict(row: pd.Series) -> dict:
    d = row.to_dict()
    return {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in d.items()}


def _fmt_amount(v) -> str:
    try:
        return f"{float(v):,.2f}".replace(",", " ").replace(".", ",")
    except (TypeError, ValueError):
        return "?"


class RulesEngine:
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> list[str]:
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            logger.warning("Colonnes manquantes dans le DataFrame : %s", missing)
        return missing

    # ------------------------------------------------------------------
    # MOTEUR 1 : RÈGLES DÉTERMINISTES (motifs suspects connus)
    # ------------------------------------------------------------------
    @staticmethod
    def _rule_engine(df: pd.DataFrame) -> list:
        anomalies = []
        safe_amount = df['amount'] if 'amount' in df.columns else pd.Series(dtype=float)
        safe_vendor = df['vendor'] if 'vendor' in df.columns else pd.Series(dtype=str)
        safe_date = df['date'] if 'date' in df.columns else pd.Series(dtype=str)

        # Règle R1 : Transactions en double (mêmes montant + date + fournisseur)
        dup_cols = [c for c in ['amount', 'date', 'vendor'] if c in df.columns]
        if dup_cols:
            dupes = df[df.duplicated(subset=dup_cols, keep=False)]
            for _, row in dupes.iterrows():
                anomalies.append({
                    "type": "Trans.En double",
                    "severity": "high",
                    "confidence": 0.85,
                    "description": f"Transaction en double : {_fmt_amount(row.get('amount'))} CDF",
                    "reference": _safe_dict(row),
                    "summary": "Une transaction identique existe déjà (même montant, date et fournisseur).",
                    "reason": "Deux écritures présentent exactement le même montant, la même date et le même fournisseur.",
                    "red_flags": ["Duplicata exact", "Risque de double paiement"],
                    "suggested_action": "Vérifier si la transaction a déjà été payée et annuler le doublon.",
                })

        # Règle R2 : Montants ronds élevés (>= 10000, multiple de 1000)
        if 'amount' in df.columns:
            large_round = df[(df['amount'] >= 10000) & (df['amount'] % 1000 == 0)]
            for _, row in large_round.iterrows():
                anomalies.append({
                    "type": "Montant rond élevé",
                    "severity": "medium",
                    "confidence": 0.5,
                    "description": f"Montant rond élevé : {_fmt_amount(row['amount'])} CDF — vérifier l'approbation",
                    "reference": _safe_dict(row),
                    "summary": "Un montant rond et élevé peut masquer un paiement non approuvé.",
                    "reason": f"Le montant {_fmt_amount(row['amount'])} CDF est rond et supérieur au seuil d'alerte.",
                    "red_flags": ["Montant rond", "Montant élevé"],
                    "suggested_action": "Confirmer l'existence d'une pièce justificative et d'une validation hiérarchique.",
                })

        # Règle R3 : Taux de TVA invalide
        if 'tax_rate' in df.columns and 'amount' in df.columns:
            invalid_tax = df[(df['tax_rate'] > 0.25) | (df['tax_rate'] < 0)]
            for _, row in invalid_tax.iterrows():
                anomalies.append({
                    "type": "TVA invalide",
                    "severity": "critical",
                    "confidence": 0.9,
                    "description": f"Taux de TVA invalide : {row['tax_rate']}%",
                    "reference": _safe_dict(row),
                    "summary": "Un taux de TVA hors des bornes autorisées (0–25%) a été détecté.",
                    "reason": f"Le taux enregistré est de {row['tax_rate']}%, hors de la plage SYSCOHADA/OHADA usuelle.",
                    "red_flags": ["TVA hors plage", "Risque fiscal"],
                    "suggested_action": "Corriger le taux de TVA conformément à la réglementation en vigueur.",
                })

        # Règle R4 : Fournisseurs non approuvés / à risque
        if 'vendor' in df.columns:
            blacklisted = df[df['vendor'].astype(str).str.upper().isin(BLACKLISTED_VENDORS)]
            for _, row in blacklisted.iterrows():
                anomalies.append({
                    "type": "Fournisseur à risque",
                    "severity": "critical",
                    "confidence": 0.9,
                    "description": f"Fournisseur non approuvé : {row['vendor']}",
                    "reference": _safe_dict(row),
                    "summary": "Paiement vers un fournisseur figurant sur la liste à risque.",
                    "reason": f"Le fournisseur « {row['vendor']} » est en liste de surveillance.",
                    "red_flags": ["Fournisseur interdit", "Blanchiment potentiel"],
                    "suggested_action": "Interrompre le paiement et ouvrir une enquête de contrôle interne.",
                })

        # Règle R5 : Transactions négatives (réductions/avoirs non justifiés)
        if 'amount' in df.columns:
            negative = df[df['amount'] < 0]
            for _, row in negative.iterrows():
                anomalies.append({
                    "type": "Transaction négative",
                    "severity": "low",
                    "confidence": 0.4,
                    "description": f"Transaction négative : {_fmt_amount(row['amount'])} CDF — à justifier",
                    "reference": _safe_dict(row),
                    "summary": "Une écriture négative représente un avoir ou une annulation à justifier.",
                    "reason": f"Le montant {_fmt_amount(row['amount'])} CDF est négatif.",
                    "red_flags": ["Avoir non justifié"],
                    "suggested_action": "Justifier l'écriture négative par une pièce comptable correspondante.",
                })

        return anomalies

    # ------------------------------------------------------------------
    # MOTEUR 2 : MOTEUR STATISTIQUE (outliers par écart-type / z-score)
    # Approche "baseline personnelle" : chaque montant comparé à sa propre série.
    # ------------------------------------------------------------------
    @staticmethod
    def _statistical_engine(df: pd.DataFrame) -> list:
        anomalies = []
        if 'amount' not in df.columns:
            return anomalies

        amount = df['amount'].astype(float)
        if amount.empty or amount.nunique() < 5:
            return anomalies

        mean = amount.mean()
        std = amount.std()
        if std == 0 or np.isnan(std) or mean == 0:
            return anomalies

        # z-score : (x - moyenne) / écart-type. |z| >= 3 => hors norme
        zscores = ((amount - mean) / std).abs()
        outliers = df[zscores >= 3]

        for _, row in outliers.iterrows():
            z = zscores.loc[row.name]
            anomalies.append({
                "type": "Écart statistique",
                "severity": "high",
                "confidence": min(0.95, 0.55 + z * 0.08),
                "description": f"Montant hors norme : {_fmt_amount(row['amount'])} CDF (écart-type {z:.1f})",
                "reference": _safe_dict(row),
                "summary": "Le montant s'écarte fortement de la moyenne des autres transactions.",
                "reason": f"Montant de {_fmt_amount(row['amount'])} CDF pour un écart-type de {z:.1f} (seuil ≥ 3).",
                "red_flags": ["Valeur aberrante", "Écart > 3σ"],
                "suggested_action": "Justifier le montant anormal ou vérifier une erreur de saisie/fraude.",
            })

        return anomalies

    # ------------------------------------------------------------------
    # MOTEUR 3 (léger) : détection de schémas "fractionnement de seuil"
    # Plusieurs petits montants juste sous un seuil (ex: 5000 CDF).
    # ------------------------------------------------------------------
    @staticmethod
    def _splitting_engine(df: pd.DataFrame) -> list:
        anomalies = []
        if 'amount' not in df.columns or 'vendor' not in df.columns:
            return anomalies

        threshold = 5000
        # groupé par fournisseur ET par date : plusieurs lignes juste sous le seuil
        df = df.copy()
        df['near'] = (df['amount'] > 0) & (df['amount'] <= threshold) & (df['amount'] >= threshold * 0.6)
        if 'date' in df.columns:
            grouped = df[df['near']].groupby(['vendor', 'date'], dropna=False)
        else:
            grouped = df[df['near']].groupby('vendor', dropna=False)

        for (vendor, *_), g in grouped:
            if len(g) >= 3:
                total = g['amount'].sum()
                if total >= threshold * 2:
                    anomalies.append({
                        "type": "Fractionnement de seuil",
                        "severity": "high",
                        "confidence": 0.75,
                        "description": f"{len(g)} paiements à {vendor} cumulés à {_fmt_amount(total)} CDF",
                        "reference": {"vendor": vendor, "count": int(len(g)), "total": float(total)},
                        "summary": "Plusieurs paiements juste sous le seuil pourraient contourner une validation.",
                        "reason": f"{len(g)} montants proches du seuil (≤ {threshold} CDF) culminent à {_fmt_amount(total)} CDF pour {vendor}.",
                        "red_flags": ["Contournement de seuil", "Éclatement de facture"],
                        "suggested_action": "Consolider ces paiements et vérifier la validation d'approbation globale.",
                    })

        return anomalies

    # ------------------------------------------------------------------
    # ORCHESTREUR / DECISION ENGINE : fusionne les moteurs
    # ------------------------------------------------------------------
    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> list:
        anomalies = []
        if df.empty:
            return anomalies

        missing = RulesEngine._validate_columns(df)
        if missing:
            anomalies.append({
                "type": "Qualité des données",
                "severity": "critical",
                "confidence": 1.0,
                "description": f"Colonnes manquantes : {', '.join(missing)}. Analyse partielle.",
                "reference": {},
                "summary": "Le fichier ne contient pas toutes les colonnes attendues.",
                "reason": f"Colonnes manquantes : {', '.join(missing)}.",
                "red_flags": ["Données incomplètes"],
                "suggested_action": "Fournir un fichier complet avec les colonnes montant, date, fournisseur.",
            })

        # Lancer les trois moteurs
        rule_anoms = RulesEngine._rule_engine(df)
        stat_anoms = RulesEngine._statistical_engine(df)
        split_anoms = RulesEngine._splitting_engine(df)

        anomalies.extend(rule_anoms)
        anomalies.extend(stat_anoms)
        anomalies.extend(split_anoms)

        # Tri par sévérité (critical -> low)
        anomalies.sort(key=lambda x: SEVERITY_ORDER.get(x.get('severity'), 4))
        return anomalies

    @staticmethod
    def calculate_risk_score(anomalies: list, total_rows: int) -> float:
        if total_rows == 0:
            return 0.0

        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        # On pondère aussi par la confiance du moteur
        total_score = sum(
            weights.get(a['severity'], 1) * a.get('confidence', 1.0)
            for a in anomalies
        )

        raw_score = (total_score / max(1, total_rows)) * 100
        return min(100, round(raw_score, 2))
