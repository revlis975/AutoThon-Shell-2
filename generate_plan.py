import json, yaml, pandas as pd, os, smtplib
from email.message import EmailMessage
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
with open("TestResults/plan.json", "w") as f:
    json.dump(plan, f, indent=2)

print(f"Processed {len(plan)} incidents. Plan saved to plan.json")

df = pd.read_json("TestResults/plan.json")
df.to_csv("TestResults/plan.csv", index=False)

def send_email_with_attachments(
    smtp_server, port, sender_email, sender_password,
    receiver_email, subject
):
    # Fixed attachments (replace with your actual paths)
    attachment_paths = [
        "TestResults/plan.csv"
    ]

    # Pre-filled business email body
    body = """\
Hello Team,

We recently faced a large number of failing test incidents that were slowing release decisions. To bring order and speed to the process, we created a clear plan that sets time limits and priority for each issue. This removed manual guesswork and let the QA team focus on the most important problems first.

The attached report lists every incident, the minutes recommended for retesting, and the order in which they should be addressed.

Best regards,  
Shell - 2 QA Engineers.
"""

    # Compose email
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.set_content(body)

    # Attach files
    for path in attachment_paths:
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                file_data = file.read()
                file_name = os.path.basename(path)
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
        else:
            print(f"[!] Warning: Attachment not found or invalid path - {path}")

    # Send email
    try:
        with smtplib.SMTP_SSL(smtp_server, port) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("\n[INFO] Email sent successfully.")
    except Exception as e:
        print("\n[ERROR] Failed to send email:", e)

# ------------------- MAIN -------------------

smtp_server = 'smtp.gmail.com'
port = 465
sender_email = "guptaryan975@gmail.com"
sender_password = "mmkf lnsa uvds opab"
# receiver_email = input("Enter recipient email: ")
receiver_email = "adarsh.shukla@shell.com"
subject = "Testing Incident Report – Summary and Next Steps"

send_email_with_attachments(
    smtp_server, port, sender_email, sender_password,
    receiver_email, subject
)
