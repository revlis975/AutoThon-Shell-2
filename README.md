# AutoThon-Shell-2

# Test Incident Plan Generator

## How to Run

1. Place `policy.yaml` and `failures.jsonl` in the same directory as `generate_plan.py`.
2. Run:
   ```
   python generate_plan.py
   ```
3. Output: `plan.json` in the same directory.

## Output Format

Each entry in `plan.json` contains:
- `test_id` (if available)
- `module`
- `environment`
- `failure_type`
- `impacted_layers`
- `base_minutes`
- `final_minutes`
- `priority_score` (rounded to 3 decimals)

Sorted by `priority_score` (descending), then `module` (ascending).

## Assumptions

- Unknown `module`, `environment`, or `failure_type` use default values as per the prompt.
- If `impacted_layers` is empty, no testing is needed (`base_minutes` and `final_minutes` are 0).
- The structure of `policy.yaml`:
  ```yaml
  layer_minutes:
    layer1: 10
    layer2: 20
  environment_multiplier:
    prod: 2.0
    dev: 1.0
  failure_type_multiplier:
    crash: 1.5
    timeout: 1.2
  module_priority:
    modA: 5
    modB: 3
  upper_cap_minutes: 120
  ```
- The structure of each line in `failures.jsonl`:
  ```json
  {
    "test_id": "T123",
    "module": "modA",
    "environment": "prod",
    "failure_type": "crash",
    "impacted_layers": ["layer1", "layer2"]
  }
  ```

## Minimal Unit Test Example

You can add this at the bottom of the script for basic validation:

```python
def test_compute_base_minutes():
    policy = {'layer_minutes': {'l1': 10, 'l2': 20}}
    assert compute_base_minutes(policy, ['l1', 'l2']) == 30
    assert compute_base_minutes(policy, ['l3']) == 0
    assert compute_base_minutes(policy, []) == 0
```