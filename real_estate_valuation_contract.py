# CONTRACT 23 — Real Estate Valuation Oracle
# Use-case: Fetches property listings data from the web and uses LLM to
# estimate fair market value with comparable analysis.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class RealEstateValuationOracle(gl.Contract):
    region: str
    valuations: TreeMap[str, str]
    total_valuations: gl.u256
 
    def __init__(self, region: str):
        self.region = region
        self.total_valuations = gl.u256(0)
 
    @gl.public.write
    def valuate_property(
        self,
        property_description: str,
        comps_url: str,
        asking_price: int,
    ) -> dict:
        """
        Fetches comparable sales and estimates fair market value using LLM.
        """
        self.total_valuations = gl.u256(int(self.total_valuations) + 1)
        prop_id = f"prop_{int(self.total_valuations)}"
 
        def nondet() -> str:
            comps_data = ""
            try:
                response = gl.nondet.web.get(comps_url)
                comps_data = response.body.decode("utf-8")[:3000]
            except Exception:
                comps_data = "(Comps URL not accessible)"
 
            prompt = (
                f"Region: {self.region}\n"
                f"Property: {property_description}\n"
                f"Asking Price: {asking_price}\n\n"
                f"Comparable Sales Data:\n{comps_data}\n\n"
                "Estimate fair market value based on comparables.\n"
                'Respond ONLY with JSON:\n'
                '{"estimated_value": int, "value_range_low": int, "value_range_high": int, '
                '"overpriced": true|false, "price_difference_pct": float, '
                '"key_factors": [str], "confidence": "low"|"medium"|"high", "analysis": str}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["prop_id"] = prop_id
        result["asking_price"] = asking_price
        self.valuations[prop_id] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_valuation(self, prop_id: str) -> dict:
        if prop_id not in self.valuations:
            return {}
        return json.loads(self.valuations[prop_id])
 
