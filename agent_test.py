from dotenv import load_dotenv
load_dotenv()

import json, sys
from tinyfish import TinyFish

c = TinyFish()

SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "status": {"type": "string"},
                    "registration_number": {"type": "string"},
                    "incorporation_date": {"type": "string"},
                    "address": {"type": "string"},
                    "record_url": {"type": "string"},
                },
                "required": ["name", "status"],
            },
        }
    },
    "required": ["candidates"],
}

name = sys.argv[1] if len(sys.argv) > 1 else "Tesco"

resp = c.agent.run(
    goal=(
        f"Search for the company '{name}'. Return up to 5 matching companies. "
        "For each, copy the company name, status (e.g. Active, Dissolved), "
        "company number, incorporation date, registered address and the URL of its page "
        "EXACTLY as shown on the site. Do not guess. If nothing matches, return an empty list."
    ),
    url="https://find-and-update.company-information.service.gov.uk/",
    output_schema=SCHEMA,
)

print("STATUS:", resp.status)
print("STEPS:", resp.num_of_steps)
print(json.dumps(resp.result, indent=2, default=str))
if resp.error:
    print("ERROR:", resp.error)
