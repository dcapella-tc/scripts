import json

from pathlib import Path

from keys.success import BASE_URL, TC_API_ID, TC_SECRET

from jsonl_gz_writer import compressed_jsonl_writer
from threatconnect_api import ThreatConnectAPI

OUTPUT_PATH = Path("exports/indicators.jsonl.gz")


def main() -> None:
    tc = ThreatConnectAPI(base_url=BASE_URL, access_id=TC_API_ID, secret_key=TC_SECRET)
    owners = tc.get_owners()
    owner_ids = [owner["id"] for owner in owners["data"]["owner"]]
    owner_names = [owner["name"] for owner in owners["data"]["owner"]]
    with compressed_jsonl_writer(OUTPUT_PATH) as writer:
        for owner_id, owner_name in zip(owner_ids, owner_names):
            tql = f"owner = {owner_id}"
            indicators = tc.get_indicators(
                params={
                    "resultLimit": "1",
                    "tql": tql,
                    "fields": "associatedGroups,associatedIndicators,associatedArtifacts,associatedCases,attributes,customAssociations,securityLabels,tags",
                }
            )
            # writer.write({"ownerId": owner_id, "ownerName": owner_name, "tql": tql, "response": indicators})
            print(json.dumps(indicators, indent=2, sort_keys=True))
            break  # TESTING: remove to process all owners


if __name__ == "__main__":
    main()

