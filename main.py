import json

from keys.success import BASE_URL, TC_API_ID, TC_SECRET

from threatconnect_api import ThreatConnectAPI


def main() -> None:
    tc = ThreatConnectAPI(base_url=BASE_URL, access_id=TC_API_ID, secret_key=TC_SECRET)
    # owners = tc.get_owners()
    # print(json.dumps(owners, indent=2, sort_keys=True))
    tql = 'typeName = "Address"'
    indicators = tc.get_indicators(params={"tql": tql})
    print(json.dumps(indicators, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

