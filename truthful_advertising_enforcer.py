# CONTRACT 29 — Truthful Advertising Enforcer
# Use-case: Brands submit ad copy; LLM checks if claims are substantiated,
# misleading, or in violation of FTC-style truth-in-advertising standards.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class AdvertisingEnforcer(gl.Contract):
    standard: str  # e.g. "FTC", "ASA", "EU_Unfair_Commercial_Practices"
    reviews: TreeMap[str, str]
    total_reviewed: gl.u256
    violations_found: gl.u256
 
    def __init__(self, standard: str):
        self.standard = standard
        self.total_reviewed = gl.u256(0)
        self.violations_found = gl.u256(0)
 
    @gl.public.write
    def review_ad(self, ad_copy: str, product_category: str, substantiation_url: str) -> dict:
        """
        Reviews ad copy for truthfulness and substantiation compliance.
        """
        ad_hash = hashlib.sha256(ad_copy.encode()).hexdigest()[:20]
        if ad_hash in self.reviews:
            return json.loads(self.reviews[ad_hash])
 
        self.total_reviewed = gl.u256(int(self.total_reviewed) + 1)
 
        def nondet() -> str:
            substantiation = ""
            try:
                response = gl.nondet.web.get(substantiation_url)
                substantiation = response.body.decode("utf-8")[:2000]
            except Exception:
                substantiation = "(No substantiation provided or accessible)"
 
            prompt = (
                f"Advertising Standard: {self.standard}\n"
                f"Product Category: {product_category}\n\n"
                f"Ad Copy:\n{ad_copy}\n\n"
                f"Substantiation Evidence:\n{substantiation}\n\n"
                "Evaluate this ad for compliance. Check: false claims, unsubstantiated superlatives, "
                "misleading omissions, prohibited claims for this category.\n"
                'Respond ONLY with JSON:\n'
                '{"compliant": true|false, "violation_severity": "none"|"minor"|"major", '
                '"violations": [{"claim": str, "issue": str, "rule_violated": str}], '
                '"recommendations": [str], "overall_verdict": str}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
 
        if not result["compliant"]:
            self.violations_found = gl.u256(int(self.violations_found) + 1)
 
        self.reviews[ad_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_review(self, ad_hash: str) -> dict:
        if ad_hash not in self.reviews:
            return {}
        return json.loads(self.reviews[ad_hash])
 
    @gl.public.view
    def get_stats(self) -> dict:
        return {
            "total_reviewed": int(self.total_reviewed),
            "violations_found": int(self.violations_found),
            "compliance_rate": (
                (int(self.total_reviewed) - int(self.violations_found)) / int(self.total_reviewed)
                if int(self.total_reviewed) > 0 else 1.0
            ),
        }
 
