import json
import logging
from config import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)

FALLBACK_RULES = [
    "Vérifier les seuils d'approbation",
    "Vérifier la TVA",
    "Vérifier les doublons",
]

def scout_node(state: dict):
    df = state['df']
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
        try:
            data = json.loads(response.content)
            state['rules'] = data.get("rules", FALLBACK_RULES)
        except json.JSONDecodeError as e:
            logger.warning("Réponse LLM non-JSON, fallback utilisé : %s", e)
            state['rules'] = FALLBACK_RULES
    except Exception as e:
        logger.error("Erreur Regulatory Scout (mode dégradé) : %s", e)
        state['rules'] = FALLBACK_RULES
    
    return state
