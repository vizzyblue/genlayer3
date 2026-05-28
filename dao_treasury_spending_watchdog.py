# CONTRACT 24 — DAO Treasury Spending Watchdog
# Use-case: Monitors DAO multisig transaction descriptions and flags
# suspicious or off-mission spending using LLM analysis.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class TreasuryWatchdog(gl.Contract):
    dao_mission: str
    flags: DynArray[str]
    approvals: DynArray[str]
    total_reviewed: gl.u256
 
    def __init__(self, dao_mission: str):
        self.dao_mission = dao_mission
        self.total_reviewed = gl.u256(0)
 
    @gl.public.write
    def review_transaction(
        self,
        tx_description: str,
        recipient: str,
        amount: int,
        justification: str,
    ) -> dict:
        """
        LLM reviews a treasury transaction for mission alignment and red flags.
        """
        self.total_reviewed = gl.u256(int(self.total_reviewed) + 1)
 
        prompt = (
            f"DAO Mission: {self.dao_mission}\n\n"
            f"Proposed Transaction:\n"
            f"- Description: {tx_description}\n"
            f"- Recipient: {recipient}\n"
            f"- Amount: {amount} tokens\n"
            f"- Justification: {justification}\n\n"
            "Evaluate whether this spending aligns with the DAO mission. Flag red flags.\n"
            'Respond ONLY with JSON:\n'
            '{"aligned": true|false, "risk_score": int(0-100), '
            '"red_flags": [str], "mission_alignment": int(0-100), '
            '"recommendation": "approve"|"flag"|"reject", "reasoning": str}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["recipient"] = recipient
        result["amount"] = amount
 
        entry = json.dumps(result)
        if result["recommendation"] in ("flag", "reject"):
            self.flags.append(entry)
        else:
            self.approvals.append(entry)
 
        return result
 
    @gl.public.view
    def get_flag_count(self) -> dict:
        return {
            "flagged": len(self.flags),
            "approved": len(self.approvals),
            "total": int(self.total_reviewed),
        }
 
