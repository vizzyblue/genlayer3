# CONTRACT 26 — Open Source Contribution Scorer
# Use-case: Fetches a GitHub PR or commit diff and uses LLM to score its
# quality, impact, and merit for contributor rewards.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class ContributionScorer(gl.Contract):
    project_name: str
    reward_pool: gl.u256
    scores: TreeMap[str, str]
    total_scored: gl.u256
 
    def __init__(self, project_name: str, reward_pool: int):
        self.project_name = project_name
        self.reward_pool = gl.u256(reward_pool)
        self.total_scored = gl.u256(0)
 
    @gl.public.write
    def score_contribution(self, github_pr_url: str, contributor_handle: str) -> dict:
        """
        Fetches a GitHub PR and scores the contribution quality for rewards.
        """
        self.total_scored = gl.u256(int(self.total_scored) + 1)
 
        def nondet() -> str:
            response = gl.nondet.web.get(github_pr_url)
            pr_data = response.body.decode("utf-8")[:3000]
 
            prompt = (
                f"Project: {self.project_name}\n"
                f"Contributor: {contributor_handle}\n\n"
                f"GitHub PR/Commit content:\n{pr_data}\n\n"
                "Score this open source contribution for quality and impact.\n"
                "Consider: code quality, test coverage, docs, bug fix vs feature, complexity.\n"
                'Respond ONLY with JSON:\n'
                '{"impact_score": int(0-100), "quality_score": int(0-100), '
                '"type": "bug_fix"|"feature"|"docs"|"refactor"|"security", '
                '"complexity": "low"|"medium"|"high", '
                '"reward_weight": float(0.0-1.0), "summary": str, "highlights": [str]}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["contributor"] = contributor_handle
        result["pr_url"] = github_pr_url
        self.scores[contributor_handle] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_score(self, contributor: str) -> dict:
        if contributor not in self.scores:
            return {}
        return json.loads(self.scores[contributor])
 
