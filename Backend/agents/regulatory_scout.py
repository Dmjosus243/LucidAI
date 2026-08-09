import json
from agents.llm import invoke_text

def scout_node(state: dict):
    df = state['df']
    # On prend un échantillon des colonnes pour le contexte
    sample = df.head(10).to_string()
    
    try:
        prompt = f"""
        Tu es un expert en régulation financière (SOX, IFRS). 
        Analyse cet extrait de transactions :
        {sample}
        
        Retourne les 3 règles de conformité les plus importantes à vérifier pour ce type de données.
        Réponds en JSON : {{"rules": ["règle 1", "règle 2", "règle 3"]}}
        """
        content = invoke_text(prompt)
        try:
            data = json.loads(content)
            state['rules'] = data.get("rules", [])
        except:
            state['rules'] = ["Vérifier les seuils d'approbation", "Vérifier la TVA", "Vérifier les doublons"]
    except Exception as e:
        print(f"Erreur Scout (mode dégradé): {e}")
        state['rules'] = ["Vérifier les seuils d'approbation", "Vérifier la TVA", "Vérifier les doublons"]
    
    return state