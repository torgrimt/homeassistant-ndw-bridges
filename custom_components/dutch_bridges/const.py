DOMAIN = "dutch_bridges"
CONF_BRIDGE_ID = "bridge_id"
CONF_NAME = "name"

UPDATE_INTERVAL = 300  # 5 minutes update interval to avoid hammering NDW

NDW_PLANNING_URL = "https://opendata.ndw.nu/planningsfeed_brugopeningen.xml.gz"

KNOWN_BRIDGES = {
    "NLLRU002120533900259": "Zuidhorn",
    "NLLRU002120533500201": "Noordhorn",
    "NLLRU002120533500202": "Aduard",
    # Additional prominent Dutch bridges can be added here
}
