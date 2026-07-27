import pandas as pd
import math

class RulesEngine:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> list:
        anomalies = []
        
        if df.empty:
            return anomalies

        # Règle 1 : Transactions en double (même montant, même date, même bénéficiaire)
        dupes = df[df.duplicated(subset=['amount', 'date', 'vendor'], keep=False)]
        for _, row in dupes.iterrows():
            anomalies.append({
                "type": "Duplicate Transaction",
                "severity": "high",
                "description": f"Transaction en double : {row['amount']}€ le {row['date']}",
                "reference": row.to_dict()
            })

        # Règle 2 : Montants ronds suspects (> 9999.99)
        large_round = df[(df['amount'] >= 10000) & (df['amount'] % 1000 == 0)]
        for _, row in large_round.iterrows():
            anomalies.append({
                "type": "Large Round Amount",
                "severity": "medium",
                "description": f"Montant rond élevé : {row['amount']}€ - Vérifier l'approbation",
                "reference": row.to_dict()
            })

        # Règle 3 : Écarts de TVA (si le champ tax_rate existe)
        if 'tax_rate' in df.columns and 'amount' in df.columns:
            invalid_tax = df[(df['tax_rate'] > 0.25) | (df['tax_rate'] < 0)]
            for _, row in invalid_tax.iterrows():
                anomalies.append({
                    "type": "Invalid Tax Rate",
                    "severity": "critical",
                    "description": f"Taux de TVA invalide : {row['tax_rate']}%",
                    "reference": row.to_dict()
                })

        # Règle 4 : Fournisseurs non approuvés (simulé avec une liste noire)
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

        # Règle 5 : Montants négatifs (remboursements suspects)
        negative = df[df['amount'] < 0]
        for _, row in negative.iterrows():
            anomalies.append({
                "type": "Negative Transaction",
                "severity": "low",
                "description": f"Transaction négative : {row['amount']}€ - À justifier",
                "reference": row.to_dict()
            })

        # Trier par sévérité
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return anomalies

    @staticmethod
    def calculate_risk_score(anomalies: list, total_rows: int) -> float:
        if total_rows == 0:
            return 0.0
        
        # Pondération
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_score = sum(weights.get(a['severity'], 1) for a in anomalies)
        
        # Normalisation entre 0 et 100
        raw_score = (total_score / max(1, total_rows)) * 100
        return min(100, round(raw_score, 2))