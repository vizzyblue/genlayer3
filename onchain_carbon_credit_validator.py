# CONTRACT 27 — On-Chain Carbon Credit Validator
# Use-case: Project developers submit carbon offset project descriptions;
# LLM validates additionality, permanence, and MRV compliance.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class CarbonCreditValidator(gl.Contract):
    standard: str  # "Verra VCS" | "Gold Standard" | "ACR"
    validations: TreeMap[str, str]
    total_validated: gl.u256
    total_credits_issued: gl.u256
 
    def __init__(self, standard: str):
        self.standard = standard
        self.total_validated = gl.u256(0)
        self.total_credits_issued = gl.u256(0)
 
    @gl.public.write
    def validate_project(
        self,
        project_description: str,
        methodology: str,
        claimed_credits: int,
        evidence_url: str,
    ) -> dict:
        """
        Validates a carbon offset project and determines credit issuance.
        """
        proj_hash = hashlib.sha256(project_description.encode()).hexdigest()[:20]
        self.total_validated = gl.u256(int(self.total_validated) + 1)
 
        def nondet() -> str:
            evidence = ""
            try:
                response = gl.nondet.web.get(evidence_url)
                evidence = response.body.decode("utf-8")[:2000]
            except Exception:
                evidence = "(Evidence not accessible)"
 
            prompt = (
                f"Carbon Standard: {self.standard}\n"
                f"Methodology: {methodology}\n\n"
                f"Project Description:\n{project_description}\n\n"
                f"Evidence Content:\n{evidence}\n\n"
                f"Claimed Carbon Credits: {claimed_credits} tCO2e\n\n"
                f"Validate this carbon offset project against {self.standard} requirements.\n"
                "Check: additionality, permanence, measurability, leakage, co-benefits.\n"
                'Respond ONLY with JSON:\n'
                '{"approved": true|false, "credits_approved": int, '
                '"additionality": "pass"|"fail"|"uncertain", '
                '"permanence": "pass"|"fail"|"uncertain", '
                '"measurability": "pass"|"fail"|"uncertain", '
                '"risk_discount_pct": int, "issues": [str], "summary": str}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["proj_hash"] = proj_hash
 
        if result["approved"]:
            self.total_credits_issued = gl.u256(
                int(self.total_credits_issued) + result["credits_approved"]
            )
 
        self.validations[proj_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_validation(self, proj_hash: str) -> dict:
        if proj_hash not in self.validations:
            return {}
        return json.loads(self.validations[proj_hash])
 
    @gl.public.view
    def total_credits(self) -> int:
        return int(self.total_credits_issued)
 
 
