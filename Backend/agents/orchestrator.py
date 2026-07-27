import pandas as pd
from langgraph.graph import StateGraph, END
from agents.regulatory_scout import scout_node
from agents.gap_analyst import gap_node
from agents.risk_sentinel import sentinel_node
from agents.evidence_officer import officer_node

class AuditOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(dict)
        self._build_graph()

    def _build_graph(self):
        self.workflow.add_node("scout", scout_node)
        self.workflow.add_node("gap", gap_node)
        self.workflow.add_node("sentinel", sentinel_node)
        self.workflow.add_node("officer", officer_node)
        
        self.workflow.set_entry_point("scout")
        self.workflow.add_edge("scout", "gap")
        self.workflow.add_edge("gap", "sentinel")
        self.workflow.add_edge("sentinel", "officer")
        self.workflow.add_edge("officer", END)
        
        self.app = self.workflow.compile()

    def run(self, df: pd.DataFrame, filename: str):
        initial_state = {
            "df": df,
            "filename": filename,
            "rules": "",
            "anomalies": [],
            "risk_score": 0.0,
            "report_path": ""
        }
        final_state = self.app.invoke(initial_state)
        return final_state

orchestrator = AuditOrchestrator()