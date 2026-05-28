# CONTRACT 30 — Governance Sentiment Aggregator
# Use-case: Fetches community forum discussions, social posts, or governance
# threads; LLM synthesizes community sentiment on a proposal and predicts vote.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class GovernanceSentimentAggregator(gl.Contract):
    dao_name: str
    sentiment_reports: DynArray[str]
    active_proposals: TreeMap[str, str]
    report_count: gl.u256
 
    def __init__(self, dao_name: str):
        self.dao_name = dao_name
        self.report_count = gl.u256(0)
 
    @gl.public.write
    def analyze_proposal_sentiment(
        self,
        proposal_title: str,
        proposal_text: str,
        forum_url: str,
    ) -> dict:
        """
        Fetches forum discussion and synthesizes community sentiment on a proposal.
        """
        self.report_count = gl.u256(int(self.report_count) + 1)
        report_id = f"report_{int(self.report_count)}"
 
        def nondet() -> str:
            forum_content = ""
            try:
                response = gl.nondet.web.get(forum_url)
                forum_content = response.body.decode("utf-8")[:4000]
            except Exception:
                forum_content = "(Forum data not accessible)"
 
            prompt = (
                f"DAO: {self.dao_name}\n"
                f"Proposal: {proposal_title}\n"
                f"Proposal Text: {proposal_text[:1000]}\n\n"
                f"Community Forum Discussion:\n{forum_content}\n\n"
                "Analyze the community's sentiment toward this proposal.\n"
                "Synthesize key arguments for and against. Predict likely vote outcome.\n"
                'Respond ONLY with JSON:\n'
                '{"sentiment": "strongly_for"|"for"|"neutral"|"against"|"strongly_against", '
                '"support_pct": int, "opposition_pct": int, "abstain_pct": int, '
                '"predicted_outcome": "pass"|"fail"|"uncertain", '
                '"key_arguments_for": [str], "key_arguments_against": [str], '
                '"top_concerns": [str], "summary": str, "confidence": int(0-100)}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["report_id"] = report_id
        result["proposal_title"] = proposal_title
 
        self.active_proposals[report_id] = json.dumps(result)
        self.sentiment_reports.append(json.dumps(result))
        return result
 
    @gl.public.view
    def get_report(self, report_id: str) -> dict:
        if report_id not in self.active_proposals:
            return {}
        return json.loads(self.active_proposals[report_id])
 
    @gl.public.view
    def total_reports(self) -> int:
        return int(self.report_count)
 
