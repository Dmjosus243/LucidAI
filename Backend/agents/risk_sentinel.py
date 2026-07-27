from engine.rules_engine import RulesEngine
import pandas as pd

def sentinel_node(state: dict):
    df = state['df']
    anomalies = state.get('anomalies', [])
    
    # Application des règles déterministes
    new_anomalies = RulesEngine.detect_anomalies(df)
    anomalies.extend(new_anomalies)
    
    # Calcul du score
    risk_score = RulesEngine.calculate_risk_score(anomalies, len(df))
    state['anomalies'] = anomalies
    state['risk_score'] = risk_score
    
    return state