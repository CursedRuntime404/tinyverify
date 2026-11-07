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
                    "license_type": {"type": "string"},
                    "license_number": {"type": "string"},
                    "status": {"type": "string"},
                    "issue_date": {"type": "string"},
                    "expiry_date": {"type": "string"},
                    "disciplinary_actions": {"type": "array", "items": {"type": "string"}},
                    "record_url": {"type": "string"},
                },
                "required": ["name", "status"],
            },
        }
    },
    "required": ["candidates"],
}

name = sys.argv[1] if len(sys.argv) > 1 else "Robert Smith"

resp = c.agent.run(
    goal=(
        f"Search for '{name}' using the license search form. Return up to 5 matching licenses. "
        "For each candidate, copy the licensee name, license type, license number, status (e.g. Current, Delinquent, Cancelled), "
        "issue and expiration date, and any public disciplinary actions exactly as shown on the site. "
        "Never guess. If nothing matches, return an empty candidates list. Include each record's page URL."
    ),
    url="https://search.dca.ca.gov/",
    output_schema=SCHEMA,
)

print("STATUS:", resp.status)
print("STEPS:", resp.num_of_steps)
print(json.dumps(resp.result, indent=2, default=str))
if resp.error:
    print("ERROR:", resp.error)
