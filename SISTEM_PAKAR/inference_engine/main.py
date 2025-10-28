
# inference_engine/main.py

import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RULES_PATH = os.path.join(BASE_DIR, "rules.json")


def load_kb(path=RULES_PATH):
    """Membaca knowledge base dari file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    return kb


def symptom_cf(symptom_info):
    """Hitung nilai CF gejala = MB - MD."""
    return round(symptom_info["MB"] - symptom_info["MD"], 6)


def combine_cf(cf1, cf2):
    """Kombinasi dua nilai CF untuk fakta/aturan paralel."""
    return round(cf1 + cf2 * (1 - cf1), 6)


def evaluate_rule(rule, known_facts_cf, kb_symptoms):
    """
    Evaluasi satu aturan:
    - Semua antecedent harus sudah diketahui.
    - CF akhir = kombinasi CF antecedent × CF rule.
    """
    antecedents = rule["if"]
    antecedent_cfs = []

    for a in antecedents:
        if a in known_facts_cf:
            antecedent_cfs.append(known_facts_cf[a])
        else:
            return None  

    if not antecedent_cfs:
        return None


    acc = antecedent_cfs[0]
    for c in antecedent_cfs[1:]:
        acc = combine_cf(acc, c)

   
    rule_cf = rule.get("cf", 1.0)
    final = round(acc * rule_cf, 6)
    return final


def forward_chain(kb, user_symptom_presence):
    """Melakukan inferensi forward chaining dengan certainty factor."""
    kb_symptoms = kb["symptoms"]
    known = {}

    for s, present in user_symptom_presence.items():
        if present and s in kb_symptoms:
            cf = symptom_cf(kb_symptoms[s])
            known[s] = cf

    rules = kb["rules"]
    fired = set()
    changed = True

    while changed:
        changed = False
        for rule in rules:
            rid = rule["id"]
            if rid in fired:
                continue

            antecedents = rule["if"]
            if not all(a in known for a in antecedents):
                continue

            cf_rule = evaluate_rule(rule, known, kb_symptoms)
            if cf_rule is None:
                continue

            conclusion = rule["then"]

            if conclusion in known:
                new_cf = combine_cf(known[conclusion], cf_rule)
                if new_cf != known[conclusion]:
                    known[conclusion] = new_cf
                    changed = True
            else:
                known[conclusion] = cf_rule
                changed = True

            fired.add(rid)

    return known


def pretty_results(known, kb):
    """Menampilkan hasil inferensi dalam bentuk terformat."""
    conclusions = []
    label_map = {r["then"]: r.get("then_label", r["then"]) for r in kb["rules"]}

    for fact, cf in known.items():
        if not fact.startswith("G"):  
            label = label_map.get(fact, fact)
            conclusions.append((fact, label, cf))

    conclusions.sort(key=lambda x: x[2], reverse=True)
    return conclusions
