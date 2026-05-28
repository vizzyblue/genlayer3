# CONTRACT 25 — Multilingual Smart Clause Interpreter
# Use-case: Contract parties can query what a legal clause means in plain
# language; LLM interprets and returns jurisdiction-aware explanations.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class ClauseInterpreter(gl.Contract):
    jurisdiction: str
    interpretations: TreeMap[str, str]
    total_queries: gl.u256
 
    def __init__(self, jurisdiction: str):
        self.jurisdiction = jurisdiction
        self.total_queries = gl.u256(0)
 
    @gl.public.write
    def interpret_clause(self, clause_text: str, language: str) -> dict:
        """
        Interprets a legal clause in plain language for the given jurisdiction.
        """
        clause_hash = hashlib.sha256(f"{clause_text}{language}".encode()).hexdigest()[:20]
        if clause_hash in self.interpretations:
            return json.loads(self.interpretations[clause_hash])
 
        self.total_queries = gl.u256(int(self.total_queries) + 1)
 
        prompt = (
            f"Jurisdiction: {self.jurisdiction}\n"
            f"Target Language: {language}\n\n"
            f"Legal Clause:\n{clause_text}\n\n"
            "Explain this clause in plain language. Identify obligations, rights, and risks.\n"
            'Respond ONLY with JSON:\n'
            '{"plain_explanation": str, "party_obligations": [str], "party_rights": [str], '
            '"risks": [str], "enforceability": "strong"|"moderate"|"weak"|"unknown", '
            '"key_terms": [{"term": str, "meaning": str}]}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        self.interpretations[clause_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_interpretation(self, clause_hash: str) -> dict:
        if clause_hash not in self.interpretations:
            return {}
        return json.loads(self.interpretations[clause_hash])
 
