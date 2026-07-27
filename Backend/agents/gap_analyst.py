from config import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import json

def gap_node(state: dict):
    df = state['df']
    rules = state['rules']
    anomalies = state.get('anomalies', [])
    
    if not rules:
        return state
    
    sample = df.head(20).to_string()
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=config.GEMINI_API_KEY)
        prompt = f"""
        Voici les règles : {rules}
        Voici les données : {sample}
        
        Identifie les transactions qui violent ces règles.
        Retourne une liste JSON : [{{"description": "...", "severity": "high"}}]
        """
        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            new_anomalies = json.loads(response.content)
            if isinstance(new_anomalies, list):
                for a in new_anomalies:
                    a['type'] = "Compliance Gap"
                    anomalies.append(a)
        except:
            pass
    except:
        pass
    
    state['anomalies'] = anomalies
    return state