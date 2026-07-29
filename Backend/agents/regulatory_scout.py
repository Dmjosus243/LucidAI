import json
from config import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage  # <-- IMPORT CORRIGÉ

def scout_node(state: dict):
    df = state['df']
    # On prend un échantillon des colonnes pour le contexte
    sample = df.head(10).to_string()
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=config.GEMINI_API_KEY)
        prompt = f"""
        Tu es un expert en régulation financière (SOX, IFRS). 
        Analyse cet extrait de transactions :
        {sample}
        
        Retourne les 3 règles de conformité les plus importantes à vérifier pour ce type de données.
        Réponds en JSON : {{"rules": ["règle 1", "règle 2", "règle 3"]}}
        """
        response = llm.invoke([HumanMessage(content=prompt)])
        # Fallback si le JSON est mal formé
        try:
            data = json.loads(response.content)
            state['rules'] = data.get("rules", [])
        except:
            state['rules'] = ["Vérifier les seuils d'approbation", "Vérifier la TVA", "Vérifier les doublons"]
    except Exception as e:
        print(f"Erreur Scout (mode dégradé): {e}")
        state['rules'] = ["Vérifier les seuils d'approbation", "Vérifier la TVA", "Vérifier les doublons"]
    
    return state