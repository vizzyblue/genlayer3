# CONTRACT 22 — On-Chain Brand Safety Monitor
# Use-case: Fetches webpage content and verifies whether it's brand-safe
# for ad placement, using LLM to assess IAS/GARM categories.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class BrandSafetyMonitor(gl.Contract):
    advertiser: str
    brand_guidelines: str
    safety_reports: TreeMap[str, str]
    total_scanned: gl.u256
 
    def __init__(self, advertiser: str, brand_guidelines: str):
        self.advertiser = advertiser
        self.brand_guidelines = brand_guidelines
        self.total_scanned = gl.u256(0)
 
    @gl.public.write
    def check_page(self, page_url: str) -> dict:
        """
        Checks if a webpage is brand-safe for ad placement.
        """
        url_hash = hashlib.sha256(page_url.encode()).hexdigest()[:20]
        if url_hash in self.safety_reports:
            return json.loads(self.safety_reports[url_hash])
 
        self.total_scanned = gl.u256(int(self.total_scanned) + 1)
 
        def nondet() -> str:
            response = gl.nondet.web.get(page_url)
            content = response.body.decode("utf-8")[:3000]
 
            prompt = (
                f"Advertiser: {self.advertiser}\n"
                f"Brand Guidelines: {self.brand_guidelines}\n\n"
                f"Webpage Content:\n{content}\n\n"
                "Evaluate this page for brand safety (GARM categories).\n"
                "Categories: adult, violence, hate_speech, terrorism, drugs, safe.\n"
                'Respond ONLY with JSON:\n'
                '{"brand_safe": true|false, "safety_score": int(0-100), '
                '"categories_detected": [str], "garm_tier": int(1-4), '
                '"recommendation": "place"|"avoid"|"review", "reason": str}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["url"] = page_url
        self.safety_reports[url_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_report(self, url_hash: str) -> dict:
        if url_hash not in self.safety_reports:
            return {}
        return json.loads(self.safety_reports[url_hash])
 
