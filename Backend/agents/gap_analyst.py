from agents.llm import invoke_text
import json

def gap_node(state: dict):
    df = state['df']
    rules = state['rules']
    anomalies = state.get('anomalies', [])
    
    if not rules:
        return state
    
    sample = df.head(20).to_string()
    
    try:
        prompt = f"""
        Voici les règles : {rules}
        Voici les données : {sample}
        
        Identifie les transactions qui violent ces règles.
        Retourne une liste JSON : [{{"description": "...", "severity": "high"}}]
        """
        content = invoke_text(prompt)
        try:
            new_anomalies = json.loads(content)
            if isinstance(new_anomalies, list):
                for a in new_anomalies:
                    a['type'] = "Compliance Gap"
                    anomalies.append(a)
        except:
            pass
    except Exception as e:
        print(f"Erreur Gap Analyst (mode dégradé): {e}")
    
    state['anomalies'] = anomalies
    return state