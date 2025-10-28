# inference_engine/main.py
import json
import os
from collections import defaultdict, deque

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
RULES_PATH = os.path.normpath(os.path.join(BASE_DIR, "rules.json"))

def load_kb(path=RULES_PATH):
    with open(path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    return kb

def symptom_cf(symptom_info):
    return round(symptom_info["MB"] - symptom_info["MD"], 6)

def combine_cf(cf1, cf2):
    """
    Combine two CF values for same hypothesis using CF combination formula:
    CF_comb = CF1 + CF2 * (1 - CF1)
    Works when both CFs are >=0 (paper uses positive values).
    """
    return round(cf1 + cf2 * (1 - cf1), 6)

def evaluate_rule(rule, known_facts_cf, kb_symptoms):
    """
    For a rule whose antecedents (rule['if']) may include symptom codes (Gxx)
    or previously inferred conclusions (Pxx). known_facts_cf: dict of fact->cf
    Return computed CF for rule's conclusion if antecedents satisfied (i.e., we have CF for all),
    otherwise None.
    For conjunction (AND), we combine symptom CFs using successive combination formula,
    but first we take each symptom's CF (from known_facts_cf or from kb_symptoms),
    if any antecedent missing -> rule not triggered.
    Finally multiply by rule['cf'] to reflect confidence in the rule itself.
    """
    antecedents = rule["if"]
    antecedent_cfs = []
    for a in antecedents:
        if a in known_facts_cf:
            antecedent_cfs.append(known_facts_cf[a])
        elif a in kb_symptoms:
            return None
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
    """
    kb: loaded knowledge base (dict)
    user_symptom_presence: dict symptom_code -> True/False
    Returns inferred_facts: dict fact -> cf
    """
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
            all_available = all(a in known for a in antecedents)
            if not all_available:
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
    """
    Filter conclusions (Pxx and Complication_*) from known and produce sorted list.
    """
    conclusions = []
    label_map = {}
    for r in kb["rules"]:
        label_map[r["then"]] = r.get("then_label", r["then"])
    for fact, cf in known.items():
        if not fact.startswith("G"):
            label = label_map.get(fact, fact)
            conclusions.append((fact, label, cf))
    conclusions.sort(key=lambda x: x[2], reverse=True)
    return conclusions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", default=RULES_PATH, help="Path to rules.json")
    args = parser.parse_args()

    kb = load_kb(args.kb)
    symptoms = kb["symptoms"]
    print("=== Sistem Pakar Diagnosa Osteoporosis (CLI) ===")
    print("Jawab Y jika mengalami gejala, N jika tidak.")
    user_presence = {}
    for s, info in symptoms.items():
        while True:
            ans = input(f"{s} - {info['label']} ? (Y/N) ").strip().lower()
            if ans in ("y","n"):
                user_presence[s] = (ans == "y")
                break
            else:
                print("Masukkan Y atau N.")
    known = forward_chain(kb, user_presence)
    conclusions = pretty_results(known, kb)
    if not conclusions:
        print("\nTidak ada kesimpulan yang dapat ditarik dari input.")
    else:
        print("\nHasil Diagnosa (urutan berdasarkan CF tertinggi):")
        for code, label, cf in conclusions:
            print(f"- {label} ({code}) -> Confidence: {cf*100:.2f}%")
