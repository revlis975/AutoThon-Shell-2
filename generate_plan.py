#!/usr/bin/env python3
"""
generate_plan.py

End-to-end deterministic solution for the TestAutothon 2025 challenge.

Steps implemented:
1. Load policy.yaml
2. Load failures.jsonl
3. For each incident:
      - compute Base_minutes
      - compute Final_minutes with multipliers and cap
      - compute priority_score (3-decimal rounding)
4. Sort incidents by priority_score desc, then module asc
5. Output plan.json

Usage:
    python generate_plan.py --policy Policy.yaml --failures Failures.jsonl --output plan.json
"""

import argparse
import json
import os
from decimal import Decimal, ROUND_HALF_UP

import yaml  # pip install pyyaml

# -------- Defaults --------
DEFAULT_MULTIPLIER = 1.0
DEFAULT_MODULE_PRIORITY = 1.0

# -------- Helpers --------
def round_half_up(value, places):
    return float(Decimal(value).quantize(Decimal(f"0.{ '0'* (places-1) }1"),
                                        rounding=ROUND_HALF_UP))

def load_policy(path):
    with open(path, "r", encoding="utf-8") as f:
        p = yaml.safe_load(f)
    return {
        "layer_minutes": p.get("minutes_per_impacted_layer", {}),
        "env_mult": (p.get("multipliers") or {}).get("by_environment", {}),
        "fail_mult": (p.get("multipliers") or {}).get("by_failure_type", {}),
        "module_priority": p.get("module_priority_score", {}),
        "cap": (p.get("caps") or {}).get("per_incident_minutes_max", None),
    }

def compute_plan(policy, failures_path):
    out = []
    with open(failures_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            # rec = json.loads(line)
            data = json.load(f)        # whole file is a JSON array
            for rec in data:
                module = rec.get("module")
                env = rec.get("environment")
                ftype = rec.get("failure_type")
                layers = rec.get("impacted_layers") or []
                test_id = rec.get("test_id")

            # Base minutes
            base = sum(policy["layer_minutes"].get(l, 0) for l in layers)

            # Multipliers
            em = policy["env_mult"].get(env, DEFAULT_MULTIPLIER)
            fm = policy["fail_mult"].get(ftype, DEFAULT_MULTIPLIER)

            # Final minutes with cap
            final = base * em * fm
            if policy["cap"] is not None:
                final = min(final, policy["cap"])
            final = round_half_up(final, 2)

            # Priority score
            mp = policy["module_priority"].get(module, DEFAULT_MODULE_PRIORITY)
            priority = round_half_up(mp * em * fm, 3)

            out.append({
                "test_id": test_id,
                "module": module,
                "environment": env,
                "failure_type": ftype,
                "impacted_layers": layers,
                "Base_minutes": base,
                "Final_minutes": final,
                "priority_score": priority
            })

    # sort: primary priority desc, secondary module asc
    return sorted(out, key=lambda r: (-r["priority_score"], (r["module"] or "").lower()))

def write_output(plan, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

# -------- CLI --------
def main():
    parser = argparse.ArgumentParser(description="Generate deterministic test plan.")
    parser.add_argument("--policy", required=True, help="Path to policy.yaml")
    parser.add_argument("--failures", required=True, help="Path to failures.jsonl")
    parser.add_argument("--output", default="plan.json", help="Output file path")
    args = parser.parse_args()

    policy = load_policy(args.policy)
    plan = compute_plan(policy, args.failures)
    write_output(plan, args.output)
    print(f"Wrote {len(plan)} incidents to {args.output}")

if __name__ == "__main__":
    main()
