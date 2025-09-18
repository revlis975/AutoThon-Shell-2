import json
import yaml

# -------------------------------
# Load policy.yaml
# -------------------------------
with open("TestData/policy.yaml") as f:
    policy = yaml.safe_load(f)

# Extract policy details
caps = policy.get("caps", {})
max_minutes = caps.get("per_incident_minutes_max", 60)

env_multipliers = policy.get("multipliers", {}).get("by_environment", {})
failure_multipliers = policy.get("multipliers", {}).get("by_failure_type", {})
module_priorities = policy.get("module_priority_score", {})
layer_minutes = policy.get("minutes_per_impacted_layer", {})

# -------------------------------
# Load failures.jsonl
# -------------------------------
incidents = []
with open("TestData/failures.jsonl") as f:
    for line in f:
        incidents.append(json.loads(line))

# -------------------------------
# Compute plan
# -------------------------------
plan = []

for incident in incidents:
    module = incident.get("module", "")
    environment = incident.get("environment", "")
    failure_type = incident.get("failure_type", "")
    impacted_layers = incident.get("impacted_layers", [])

    # Base minutes: sum of minutes per impacted layer
    base_minutes = sum(layer_minutes.get(layer, 0) for layer in impacted_layers)

    # Apply multipliers (default 1.0 for unknown)
    env_multiplier = env_multipliers.get(environment, 1.0)
    fail_multiplier = failure_multipliers.get(failure_type, 1.0)

    # Final minutes capped
    final_minutes = min(max_minutes, base_minutes * env_multiplier * fail_multiplier)

    # Module priority (default 1 if unknown)
    module_priority = module_priorities.get(module, 1)

    # Priority score
    priority_score = round(module_priority * env_multiplier * fail_multiplier, 3)

    plan.append({
        "test_id": incident.get("test_id"),
        "module": module,
        "environment": environment,
        "failure_type": failure_type,
        "impacted_layers": impacted_layers,
        "Base_minutes": base_minutes,
        "Final_minutes": final_minutes,
        "priority_score": priority_score
    })

# -------------------------------
# Sort: primary = priority_score desc, secondary = module asc
# -------------------------------
plan.sort(key=lambda x: (-x["priority_score"], x["module"]))

# -------------------------------
# Save to plan.json
# -------------------------------
with open("plan.json", "w") as f:
    json.dump(plan, f, indent=2)

print(f"Processed {len(plan)} incidents. Plan saved to plan.json")