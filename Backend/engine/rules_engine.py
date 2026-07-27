import pandas as pd
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["amount", "date", "vendor"]
OPTIONAL_COLUMNS = ["tax_rate"]

class RulesEngine:
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> list[str]:
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            logger.warning("Colonnes manquantes dans le DataFrame : %s", missing)
        return missing

    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> list:
        anomalies = []
        
        if df.empty:
            return anomalies

        missing = RulesEngine._validate_columns(df)
        if missing:
            anomalies.append({
                "type": "Data Quality",
                "severity": "critical",
                "description": f"Colonnes manquantes : {', '.join(missing)}. Analyse partielle.",
                "reference": {},
            })

        safe_amount = df['amount'] if 'amount' in df.columns else pd.Series(dtype=float)
        safe_vendor = df['vendor'] if 'vendor' in df.columns else pd.Series(dtype=str)
        safe_date = df['date'] if 'date' in df.columns else pd.Series(dtype=str)

        # Règle 1 : Transactions en double
        dup_cols = [c for c in ['amount', 'date', 'vendor'] if c in df.columns]
        if dup_cols:
            dupes = df[df.duplicated(subset=dup_cols, keep=False)]
            for _, row in dupes.iterrows():
                anomalies.append({
                    "type": "Duplicate Transaction",
                    "severity": "high",
                    "description": f"Transaction en double : {row.get('amount', '?')}€ le {row.get('date', '?')}",
                    "reference": row.to_dict()
                })

        # Règle 2 : Montants ronds suspects (>= 10000, multiple de 1000)
        if 'amount' in df.columns:
            large_round = df[(df['amount'] >= 10000) & (df['amount'] % 1000 == 0)]
            for _, row in large_round.iterrows():
                anomalies.append({
                    "type": "Large Round Amount",
                    "severity": "medium",
                    "description": f"Montant rond élevé : {row['amount']}€ - Vérifier l'approbation",
                    "reference": row.to_dict()
                })

        # Règle 3 : Écarts de TVA
        if 'tax_rate' in df.columns and 'amount' in df.columns:
            invalid_tax = df[(df['tax_rate'] > 0.25) | (df['tax_rate'] < 0)]
            for _, row in invalid_tax.iterrows():
                anomalies.append({
                    "type": "Invalid Tax Rate",
                    "severity": "critical",
                    "description": f"Taux de TVA invalide : {row['tax_rate']}%",
                    "reference": row.to_dict()
                })

        # Règle 4 : Fournisseurs non approuvés
        blacklist = ["UNKNOWN VENDOR", "OFFSHORE CORP", "CASH PAYMENT"]
        if 'vendor' in df.columns:
            blacklisted = df[df['vendor'].str.upper().isin(blacklist)]
            for _, row in blacklisted.iterrows():
                anomalies.append({
                    "type": "Unapproved Vendor",
                    "severity": "critical",
                    "description": f"Fournisseur non approuvé : {row['vendor']}",
                    "reference": row.to_dict()
                })

        # Règle 5 : Montants négatifs
        if 'amount' in df.columns:
            negative = df[df['amount'] < 0]
            for _, row in negative.iterrows():
                anomalies.append({
                    "type": "Negative Transaction",
                    "severity": "low",
                    "description": f"Transaction négative : {row['amount']}€ - À justifier",
                    "reference": row.to_dict()
                })

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return anomalies

    @staticmethod
    def calculate_risk_score(anomalies: list, total_rows: int) -> float:
        if total_rows == 0:
            return 0.0
        
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_score = sum(weights.get(a['severity'], 1) for a in anomalies)
        
        raw_score = (total_score / max(1, total_rows)) * 100
        return min(100, round(raw_score, 2))
