# services/daily_hexagram_service.py
import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from services.llm_service import llm

from services.hexagram_service import HexagramService

# ---------- Helper: score -> bit & moving ----------
def score_to_bit_and_moving(score: int) -> Tuple[int, bool]:
    """
    Chấm điểm 0-100 -> (bit, moving_flag)
    Quy tắc (theo bạn):
      >=70 -> Dương động (1, moving True)
      55-69 -> Dương tĩnh (1, moving False)
      46-54 -> Dương trung tính (1, moving False)
      31-45 -> Âm tĩnh (0, moving False)
      <=30 -> Âm động (0, moving True)
    """
    if score >= 70:
        return 1, True
    if 55 <= score <= 69:
        return 1, False
    if 46 <= score <= 54:
        return 1, False
    if 31 <= score <= 45:
        return 0, False
    # <=30
    return 0, True

def build_bitstring_from_h1_to_h6(bits_h1_h6: List[int]) -> str:
    """
    Input bits_h1_h6: [H1(bottom), H2, H3, H4, H5, H6(top)]
    HexagramService expects bitstring where index 0 = top-most (H6),
    so we produce bits = H6 H5 H4 H3 H2 H1
    """
    if len(bits_h1_h6) != 6:
        raise ValueError("bits_h1_h6 must have length 6")
    # reverse order: top-first
    top_first = list(reversed(bits_h1_h6))
    return "".join(str(b) for b in top_first)

def flip_bits_for_moving(bits_h1_h6: List[int], moving_flags: List[bool]) -> List[int]:
    """
    Flip bits in positions where moving_flags True.
    moving_flags aligned with H1..H6.
    """
    return [ (0 if bits_h1_h6[i]==1 else 1) if moving_flags[i] else bits_h1_h6[i] for i in range(6) ]

# ---------- Main Service ----------
class DailyHexagramService:
    """
    Create daily hexagram node by calling an LLM to score Thiên/Địa/Nhân,
    map to 6 hào, compute original & transformed hexagrams via HexagramService,
    and return detailed + compact JSON.
    """
    def __init__(self,hex_service: Optional[HexagramService] = None):
        self.llm = llm
        # use provided HexagramService or init default
        self.hex_svc = hex_service or HexagramService()

    def _prompt_for_scores(self, tien: str, dia: str, nhan: str, key_event: str) -> str:
        """
        Build a robust prompt that asks the LLM to return JSON:
        { "scores": {"H1":int,...,"H6":int}, "summary":"...", "notes": {...} }
        """
        prompt = f"""
You are an assistant that transforms environmental & human observations into six numeric scores (0-100)
for a daily I Ching-style reading. Use the following inputs and produce ONLY valid JSON (no extra text).

Inputs:
- Thiên: {tien}
- Địa: {dia}
- Nhân: {nhan}
- Key Event: {key_event}

Mapping (informational, do NOT repeat): H1 (External Force), H2 (Flow/Moisture), H3 (Activity/Energy),
H4 (Stability/Cohesion), H5 (Resources/Capacity), H6 (Stress/Threat).

Output JSON structure:
{{
  "scores": {{
    "H1": <int 0-100>,
    "H2": <int>,
    "H3": <int>,
    "H4": <int>,
    "H5": <int>,
    "H6": <int>
  }},
  "summary": "<short (1-2 sentences) natural-language summary>",
  "key_event_effect": "<one-sentence how key event affects the reading>"
}}

Choose scores consistent with inputs. Keep JSON compact.
"""
        return prompt

    def _call_llm_for_scores(self, tien: str, dia: str, nhan: str, key_event: str) -> Dict[str, Any]:
        prompt = self._prompt_for_scores(tien, dia, nhan, key_event)
        # Use predict to get string response (depends on langchain version)
        resp = llm.invoke(prompt)
        resp_text = resp.content  # <-- thay vì dùng trực tiếp resp
        # try parse JSON robustly
        try:
            data = json.loads(resp_text)
            return data
        except Exception:
            # fallback: attempt to extract first {...} block
            start = resp_text.find("{")
            end = resp_text.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(resp_text[start:end+1])
                    return data
                except Exception as e:
                    raise ValueError(f"LLM returned non-JSON response. Raw:\n{resp_text}") from e
            raise ValueError(f"LLM returned non-JSON response. Raw:\n{resp_text}")

    def create_daily_node(self, tien: str, dia: str, nhan: str, key_event: str, node_id: Optional[str]=None) -> Dict[str, Any]:
        """
        Main entry:
        - call LLM to get 6 scores
        - map scores -> bits + moving flags
        - create base & transformed hexagram (if any moving)
        - query hex_service for names & relations
        - return combined node dict (detailed + compact)
        """
        # 1) call LLM
        llm_out = self._call_llm_for_scores(tien, dia, nhan, key_event)
        scores = llm_out.get("scores")
        if not scores or not all(k in scores for k in ["H1","H2","H3","H4","H5","H6"]):
            raise ValueError("LLM output missing scores H1..H6")

        # 2) map score -> bit & moving flags (H1..H6 order)
        bits_h1_h6 = []
        moving_flags = []
        for i in range(1,7):
            sc = int(scores[f"H{i}"])
            bit, moving = score_to_bit_and_moving(sc)
            bits_h1_h6.append(bit)
            moving_flags.append(moving)

        # 3) build bitstrings in hex_service convention (top-first)
        base_bitstr = build_bitstring_from_h1_to_h6(bits_h1_h6)
        transformed_bitstr = None
        transformed_bits_h1_h6 = None
        if any(moving_flags):
            flipped = flip_bits_for_moving(bits_h1_h6, moving_flags)
            transformed_bits_h1_h6 = flipped
            transformed_bitstr = build_bitstring_from_h1_to_h6(flipped)

        # 4) lookup ids & names
        hex_bs = self.hex_svc.bitstrings  # list of 64 bitstrings in service
        if base_bitstr in hex_bs:
            base_idx = hex_bs.index(base_bitstr)
            base_node = self.hex_svc.get_node(base_idx)
        else:
            raise ValueError("Base bitstring not found in hexagram service")

        transformed_node = None
        if transformed_bitstr:
            if transformed_bitstr in hex_bs:
                tidx = hex_bs.index(transformed_bitstr)
                transformed_node = self.hex_svc.get_node(tidx)
            else:
                transformed_node = {"note":"transformed bitstring not found", "bits": transformed_bitstr}

        # 5) get relations (detailed and compact)
        base_relations = self.hex_svc.relations_of(base_node["name"])
        base_relations_compact = self.hex_svc.relations_compact(base_node["name"])

        transformed_relations = None
        transformed_relations_compact = None
        if transformed_node and "id" in transformed_node:
            transformed_relations = self.hex_svc.relations_of(transformed_node["name"])
            transformed_relations_compact = self.hex_svc.relations_compact(transformed_node["name"])

        # 6) assemble node
        node = {
            "node_id": node_id or f"daily-{int(time.time())}",
            "timestamp": datetime.utcnow().isoformat()+"Z",
            "input": {"Thien": tien, "Dia": dia, "Nhan": nhan, "KeyEvent": key_event},
            "llm_summary": llm_out.get("summary"),
            "llm_key_event_effect": llm_out.get("key_event_effect"),
            "scores": scores,
            "bits_h1_h6": bits_h1_h6,
            "moving_flags": moving_flags,
            "base": {
                "bitstring": base_bitstr,
                "id": base_node["id"],
                "name": base_node["name"],
                "bits": base_node["bits"],
                "relations": base_relations
            },
            "transformed": None
        }
        if transformed_node:
            node["transformed"] = {
                "bitstring": transformed_bitstr,
                "id": transformed_node.get("id"),
                "name": transformed_node.get("name"),
                "bits": transformed_node.get("bits"),
                "relations": transformed_relations
            }

        # 7) compact JSON for client
        # node["compact"] = {
        #     "base": base_relations_compact,
        #     "transformed": transformed_relations_compact
        # }

        return node


