# CONTRACT 21 — Agentic Commerce Dispute Layer
# Use-case: AI agents transacting on behalf of users can submit payment
# disputes; LLM arbitrates based on transaction logs and stated terms.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class AgentCommerceDispute(gl.Contract):
    disputes: TreeMap[str, str]
    dispute_count: gl.u256
 
    def __init__(self):
        self.dispute_count = gl.u256(0)
 
    @gl.public.write
    def file_agent_dispute(
        self,
        buyer_agent: str,
        seller_agent: str,
        service_terms: str,
        buyer_claim: str,
        seller_claim: str,
        transaction_log: str,
    ) -> dict:
        """
        Arbitrates disputes between AI agents in an agentic commerce context.
        """
        self.dispute_count = gl.u256(int(self.dispute_count) + 1)
        dispute_id = f"dispute_{int(self.dispute_count)}"
 
        prompt = (
            "You are an impartial arbiter for an AI agent commerce dispute.\n\n"
            f"Service Terms: {service_terms}\n\n"
            f"Buyer Agent ({buyer_agent}) Claim: {buyer_claim}\n\n"
            f"Seller Agent ({seller_agent}) Claim: {seller_claim}\n\n"
            f"Transaction Log:\n{transaction_log[:2000]}\n\n"
            "Determine liability and recommend resolution.\n"
            'Respond ONLY with JSON:\n'
            '{"liable_party": "buyer"|"seller"|"shared"|"neither", '
            '"buyer_refund_pct": int, "seller_payout_pct": int, '
            '"breach_found": true|false, "reasoning": str, "resolution": str}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["dispute_id"] = dispute_id
        self.disputes[dispute_id] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_dispute(self, dispute_id: str) -> dict:
        if dispute_id not in self.disputes:
            return {}
        return json.loads(self.disputes[dispute_id])
 
