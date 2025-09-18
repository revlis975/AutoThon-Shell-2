# AutoThon-Shell-2

## TestAutothon — deterministic plan generator

Prereqs:
- Python 3.8+
- pip install pyyaml

Files required:
- policy.yaml (policy file). Example: /mnt/data/Policy.yaml. :contentReference[oaicite:4]{index=4}
- failures.jsonl (one JSON object per line). Must include at least: module, environment, failure_type, impacted_layers. See spec. :contentReference[oaicite:5]{index=5}

Run:
$ python generate_plan.py --policy /mnt/data/Policy.yaml --failures /mnt/data/Failures.jsonl --output /mnt/data/plan.json

Output:
- plan.json: array of incident objects with fields:
  test_id, module, environment, failure_type, impacted_layers,
  Base_minutes, Final_minutes, priority_score (3 decimals)

Assumptions:
- Unknown environment or failure_type → multiplier = 1.0.
- Unknown module → priority = 1.0.
- Unknown impacted layer contributes 0 minutes.
- If impacted_layers is empty or missing → Base_minutes = 0 and Final_minutes = 0.
- Final_minutes rounded to 2 decimals.
- priority_score rounded to 3 decimals.

Notes:
- Deterministic sorting: primary priority_score desc, secondary module ascending.
- No network calls. No external services.