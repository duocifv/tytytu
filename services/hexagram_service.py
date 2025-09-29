# services/hexagram_service.py
import networkx as nx
from typing import Optional, Tuple, Dict, Any, List
import json

class HexagramService:
    """
    HexagramService (King-Wen names + Wuxing support rule).
    - MultiGraph but avoid duplicate same-relation edges.
    - Names follow King-Wen order (index 0..63 -> hexagram 1..64).
    - Element of a hexagram = element of its TOP3 (upper trigram).
    - Support: A -> B if element(A) generates element(B) in Wuxing.
    - Provides detailed relations and a compact JSON (ids only).
    """

    def __init__(self, names: Optional[List[str]] = None):
        self.G = nx.MultiGraph()
        # King-Wen order names (Chinese, pinyin, English). Index 0 -> hexagram 1.
        self.hexagram_names = names or [
            "乾 Qián - The Creative",
            "坤 Kūn - The Receptive",
            "屯 Zhūn - Difficulty at the Beginning",
            "蒙 Méng - Youthful Folly",
            "需 Xū - Waiting (Attending)",
            "訟 Sòng - Conflict",
            "師 Shī - The Army",
            "比 Bǐ - Holding Together",
            "小畜 Xiǎo Xù - Taming the Power of the Small",
            "履 Lǚ - Treading (Conduct)",
            "泰 Tài - Peace",
            "否 Pǐ - Standstill (Stagnation)",
            "同人 Tóng Rén - Fellowship with Men",
            "大有 Dà Yǒu - Possession in Great Measure",
            "謙 Qiān - Modesty",
            "豫 Yù - Enthusiasm",
            "隨 Suí - Following",
            "蠱 Gǔ - Work on the Decayed",
            "臨 Lín - Approach",
            "觀 Guān - Contemplation (Viewing)",
            "噬嗑 Shì Kè - Biting Through",
            "賁 Bì - Grace (Adorning)",
            "剝 Bō - Splitting Apart",
            "復 Fù - Return (Turning Back)",
            "無妄 Wú Wàng - Innocence (The Unexpected)",
            "大畜 Dà Xù - Great Taming",
            "頤 Yí - Corners of the Mouth (Nourishment)",
            "大過 Dà Guò - Preponderance of the Great",
            "坎 Kǎn - The Abysmal (Water)",
            "離 Lí - The Clinging (Fire)",
            "咸 Xián - Influence (Conjoining)",
            "恒 Héng - Duration",
            "遯 Dùn - Retreat",
            "大壯 Dà Zhuàng - Great Power",
            "晉 Jìn - Progress (Advancement)",
            "明夷 Míng Yí - Darkening of the Light",
            "家人 Jiā Rén - The Family",
            "睽 Kuí - Opposition",
            "蹇 Jiǎn - Obstruction (Difficulty)",
            "解 Xiè - Deliverance",
            "損 Sǔn - Decrease",
            "益 Yì - Increase",
            "夬 Guài - Breakthrough (Resolution)",
            "姤 Gòu - Coming to Meet",
            "萃 Cuì - Gathering Together (Massing)",
            "升 Shēng - Pushing Upward",
            "困 Kùn - Oppression (Exhaustion)",
            "井 Jǐng - The Well",
            "革 Gé - Revolution (Molting)",
            "鼎 Dǐng - The Cauldron",
            "震 Zhèn - The Arousing (Shock, Thunder)",
            "艮 Gèn - Keeping Still (Mountain)",
            "漸 Jiàn - Development (Gradual Progress)",
            "歸妹 Guī Mèi - The Marrying Maiden",
            "豐 Fēng - Abundance (Fullness)",
            "旅 Lǚ - The Wanderer",
            "巽 Xùn - The Gentle (Penetrating, Wind)",
            "兌 Duì - The Joyous (Lake)",
            "渙 Huàn - Dispersion (Dissolution)",
            "節 Jié - Limitation (Moderation)",
            "中孚 Zhōng Fú - Inner Truth",
            "小過 Xiǎo Guò - Preponderance of the Small",
            "既濟 Jì Jì - After Completion",
            "未濟 Wèi Jì - Before Completion"
        ]

        # bitstrings: 6-bit left=top-most hao, right=bottom-most
        self.bitstrings = [format(i, "06b") for i in range(64)]

        # map top3 bits -> trigram name (Sino-Vietnamese names possible)
        self.trigram_map = {
            "111": "Qian",  # 乾
            "000": "Kun",   # 坤
            "010": "Kan",   # 坎 (note mapping depends on bit ordering used)
            "101": "Li",    # 離
            "001": "Zhen",  # 震
            "110": "Dui",   # 兌
            "011": "Xun",   # 巽
            "100": "Gen",   # 艮
        }

        # map trigram -> Wuxing element (common fengshui mapping)
        # Qian, Dui -> Metal; Zhen, Xun -> Wood; Kun, Gen -> Earth; Li -> Fire; Kan -> Water
        self.trigram_to_element = {
            "Qian": "Metal",
            "Dui": "Metal",
            "Zhen": "Wood",
            "Xun": "Wood",
            "Kun": "Earth",
            "Gen": "Earth",
            "Li": "Fire",
            "Kan": "Water"
        }

        # Wuxing generation map: what element generates what
        self.generation = {
            "Wood": "Fire",
            "Fire": "Earth",
            "Earth": "Metal",
            "Metal": "Water",
            "Water": "Wood"
        }

        # build graph now
        self._build_graph()

    # ---------------- helpers ----------------
    def set_names(self, names: List[str]):
        if len(names) != 64:
            raise ValueError("names must have length 64")
        self.hexagram_names = names
        for i in range(64):
            if self.G.has_node(i):
                self.G.nodes[i]["name"] = names[i]

    def _get_trigram(self, bits: str) -> str:
        return self.trigram_map.get(bits[:3], "Unknown")

    def _get_element(self, bits: str) -> str:
        trig = self._get_trigram(bits)
        return self.trigram_to_element.get(trig, "Unknown")

    def _rel_exists(self, u:int, v:int, relation:str, source:Optional[int]=None, target:Optional[int]=None) -> bool:
        if not self.G.has_edge(u, v):
            return False
        data = self.G.get_edge_data(u, v)
        for k, attrs in data.items():
            if attrs.get("relation") != relation:
                continue
            if relation == "Support":
                if attrs.get("source") == source and attrs.get("target") == target:
                    return True
            else:
                return True
        return False

    def _add_rel(self, u:int, v:int, relation:str, weight:float, source:Optional[int]=None, target:Optional[int]=None):
        a, b = (min(u,v), max(u,v))
        if self._rel_exists(a, b, relation, source, target):
            return
        attrs = {"relation": relation, "weight": weight}
        if relation == "Support":
            attrs.update({"source": source, "target": target})
        self.G.add_edge(a, b, **attrs)

    # ---------------- build ----------------
    def _build_graph(self):
        # nodes
        for i in range(64):
            bits = self.bitstrings[i]
            self.G.add_node(i,
                            id=i,
                            name=self.hexagram_names[i] if i < len(self.hexagram_names) else f"Hex {i+1}",
                            bits=bits,
                            top3=bits[:3],
                            bot3=bits[3:],
                            trigram=self._get_trigram(bits),
                            element=self._get_element(bits))

        # edges
        for i in range(64):
            bits_i = self.bitstrings[i]
            top_i = bits_i[:3]

            # Opposite: invert all bits (undirected) -> i < j to add once
            opp = "".join("1" if b == "0" else "0" for b in bits_i)
            j = self.bitstrings.index(opp)
            if i < j:
                self._add_rel(i, j, "Opposite", 3.0)

            # Transform: differ by exactly 1 bit (undirected) -> add i<j
            for k in range(6):
                flipped = bits_i[:k] + ("1" if bits_i[k] == "0" else "0") + bits_i[k+1:]
                j2 = self.bitstrings.index(flipped)
                if i < j2:
                    self._add_rel(i, j2, "Transform", 1.0)

            # Ally: same top3 (undirected); j>i to add once
            for j3 in range(i+1, 64):
                if top_i == self.bitstrings[j3][:3]:
                    self._add_rel(i, j3, "Ally", 2.0)

        # Support by Wuxing: directed A -> B if element(A) generates element(B)
        for a in range(64):
            elem_a = self.G.nodes[a]["element"]
            if elem_a == "Unknown":
                continue
            generated = self.generation.get(elem_a)
            if not generated:
                continue
            # find all hexagrams whose element == generated -> a supports them
            for b in range(64):
                if a == b:
                    continue
                if self.G.nodes[b]["element"] == generated:
                    # store directed support as attrs source=a, target=b
                    self._add_rel(a, b, "Support", 2.5, source=a, target=b)

    # ---------------- public API ----------------
    def get_graph(self) -> nx.MultiGraph:
        return self.G

    def find_by_name(self, name: str) -> Tuple[Optional[int], Optional[Dict[str,Any]]]:
        for n, data in self.G.nodes(data=True):
            if data.get("name") == name:
                return n, dict(data)
        return None, None

    def relations_of(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Return detailed grouped relations:
        {
          id,name,bits,cung (trigram), element,
          relations: {
            "Opposite":[{id,name,bits,weight,relation}],
            "Transform":[...],
            "Ally":[...],
            "Support": {"in":[...], "out":[...]}
          }
        }
        """
        idx, node = self.find_by_name(name)
        if idx is None:
            return None

        groups = {"Opposite": [], "Transform": [], "Ally": [], "Support": {"in": [], "out": []}}
        for u, v, key, data in self.G.edges(idx, keys=True, data=True):
            other = v if u == idx else u
            rel = data.get("relation")
            entry = {
                "id": other,
                "name": self.G.nodes[other]["name"],
                "bits": self.G.nodes[other]["bits"],
                "trigram": self.G.nodes[other]["trigram"],
                "element": self.G.nodes[other]["element"],
                "weight": data.get("weight"),
                "relation": rel
            }
            if rel == "Support":
                src = data.get("source")
                tgt = data.get("target")
                if tgt == idx and src is not None:
                    entry["incoming"] = True
                    entry["source"] = src
                    entry["target"] = tgt
                    groups["Support"]["in"].append(entry)
                elif src == idx and tgt is not None:
                    entry["incoming"] = False
                    entry["source"] = src
                    entry["target"] = tgt
                    groups["Support"]["out"].append(entry)
                else:
                    entry["incoming"] = None
                    groups["Support"]["out"].append(entry)
            else:
                groups.setdefault(rel, []).append(entry)

        return {
            "id": idx,
            "name": node["name"],
            "bits": node["bits"],
            "trigram": node["trigram"],
            "element": node["element"],
            "relations": groups
        }

    def relations_compact(self, name: str, include: Optional[List[str]] = None) -> Optional[Dict[str, List[int]]]:
        """
        Return compact JSON of ids only.
        include: subset of ["Opposite","Transform","Ally","Support_in","Support_out"].
        If None, returns all.
        Example output:
        {
          "Opposite": [63],
          "Transform": [32,16,...],
          "Ally": [1,2,...],
          "Support_in": [32,16,...],
          "Support_out": [1,2,...]
        }
        """
        info = self.relations_of(name)
        if info is None:
            return None
        inc = set(include or ["Opposite","Transform","Ally","Support_in","Support_out"])
        out: Dict[str, List[int]] = {}
        if "Opposite" in inc:
            out["Opposite"] = [e["id"] for e in info["relations"]["Opposite"]]
        if "Transform" in inc:
            out["Transform"] = [e["id"] for e in info["relations"]["Transform"]]
        if "Ally" in inc:
            out["Ally"] = [e["id"] for e in info["relations"]["Ally"]]
        if "Support_in" in inc:
            out["Support_in"] = [e["id"] for e in info["relations"]["Support"]["in"]]
        if "Support_out" in inc:
            out["Support_out"] = [e["id"] for e in info["relations"]["Support"]["out"]]
        return out

    def describe_hexagram(self, name: str) -> str:
        info = self.relations_of(name)
        if info is None:
            return f"Không tìm thấy quẻ {name}"
        lines = [f"Quẻ {info['name']} (id={info['id']}, bits={info['bits']}, trigram={info['trigram']}, element={info['element']})\n"]
        for rel in ("Opposite","Transform","Ally"):
            lines.append(f"{rel}:")
            items = info["relations"].get(rel, [])
            if not items:
                lines.append("  - (không có)")
            else:
                for it in items:
                    lines.append(f"  - {it['name']} (id={it['id']}, bits={it['bits']}, trigram={it['trigram']}, element={it['element']}, w={it['weight']})")
            lines.append("")
        # Support
        lines.append("Support (incoming):")
        for it in info["relations"]["Support"]["in"]:
            lines.append(f"  - {it['name']} (id={it['id']}, bits={it['bits']}, element={it['element']}, source={it['source']})")
        if not info["relations"]["Support"]["in"]:
            lines.append("  - (không có)")
        lines.append("")
        lines.append("Support (outgoing):")
        for it in info["relations"]["Support"]["out"]:
            lines.append(f"  - {it['name']} (id={it['id']}, bits={it['bits']}, element={it['element']}, target={it['target']})")
        if not info["relations"]["Support"]["out"]:
            lines.append("  - (không có)")
        return "\n".join(lines)
    
    def get_node(self, idx: int) -> Optional[Dict[str, Any]]:
        """
        Trả về thông tin 1 quẻ theo index (0..63).
        Ví dụ: get_node(0) -> Quẻ 乾
        """
        if idx not in self.G.nodes:
            return None
        return dict(self.G.nodes[idx])

# ---------------- quick run example ----------------
if __name__ == "__main__":
    svc = HexagramService()
    # if you want VN names (Sino-Vietnamese) or your own King-Wen list, call:
    # svc.set_names(your_64_list)

    info = svc.relations_of("乾 Qián - The Creative")
    print("=== JSON (detailed relations_of) ===")
    print(json.dumps(info, ensure_ascii=False, indent=2))

    print("\n=== Compact (ids only) ===")
    print(json.dumps(svc.relations_compact("乾 Qián - The Creative"), ensure_ascii=False, indent=2))

    print("\n=== Mô tả gọn ===")
    print(svc.describe_hexagram("乾 Qián - The Creative"))
