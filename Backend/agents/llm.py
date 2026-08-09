from config import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


def get_llm():
    return ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, api_key=config.GEMINI_API_KEY)


def invoke_text(prompt: str) -> str:
    """Appelle le LLM et renvoie le texte brut (robuste face aux formats de réponse)."""
    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(p for p in parts if p)
    return str(content)
