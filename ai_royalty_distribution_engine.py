# CONTRACT 28 — AI Royalty Distribution Engine
# Use-case: Fetches streaming/sales data for creative works and uses LLM to
# calculate fair royalty splits among multiple collaborators.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class RoyaltyDistributor(gl.Contract):
    work_title: str
    collaborators: DynArray[str]
    contribution_descriptions: TreeMap[str, str]
    distributions: DynArray[str]
    total_distributed: gl.u256
 
    def __init__(self, work_title: str):
        self.work_title = work_title
        self.total_distributed = gl.u256(0)
 
    @gl.public.write
    def register_collaborator(self, collaborator_address: str, role_description: str):
        """Registers a collaborator and their contribution role."""
        self.collaborators.append(collaborator_address)
        self.contribution_descriptions[collaborator_address] = role_description
 
    @gl.public.write
    def distribute_royalties(self, total_revenue: int, sales_data_url: str) -> dict:
        """
        Fetches sales data and uses LLM to calculate fair royalty splits.
        """
        collab_list = [
            {"address": c, "role": self.contribution_descriptions.get(c, "Unknown")}
            for c in self.collaborators
        ]
 
        def nondet() -> str:
            sales_data = ""
            try:
                response = gl.nondet.web.get(sales_data_url)
                sales_data = response.body.decode("utf-8")[:2000]
            except Exception:
                sales_data = "(Sales data not accessible)"
 
            prompt = (
                f"Work: {self.work_title}\n"
                f"Total Revenue: {total_revenue} tokens\n\n"
                f"Collaborators:\n{json.dumps(collab_list, indent=2)}\n\n"
                f"Sales/Streaming Data:\n{sales_data}\n\n"
                "Calculate a fair royalty split based on roles and contribution types.\n"
                'Respond ONLY with JSON:\n'
                '{"splits": [{"address": str, "role": str, "pct": float, "amount": int}], '
                '"reasoning": str, "methodology": str}\n'
                "Ensure pct values sum to 100. No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["total_revenue"] = total_revenue
        self.total_distributed = gl.u256(int(self.total_distributed) + total_revenue)
        self.distributions.append(json.dumps(result))
        return result
 
    @gl.public.view
    def get_latest_distribution(self) -> dict:
        if not self.distributions:
            return {}
        return json.loads(self.distributions[-1])
 
