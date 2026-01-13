"""Constants for U-tec Local Gateway."""

VERSION = "1.4.0"
DOMAIN = "uteclocal"
NAME = "U-tec Local Gateway"

# API Configuration
DEFAULT_API_BASE_URL = "https://api.u-tec.com"
DEFAULT_OAUTH_BASE_URL = "https://oauth.u-tec.com"
DEFAULT_ACTION_PATH = "/action"
DEFAULT_SCOPE = "openapi"

# Token Refresh Configuration
DEFAULT_STATUS_POLL_INTERVAL = 60  # seconds
DEFAULT_AUTO_REFRESH_ENABLED = True
DEFAULT_REFRESH_BUFFER_MINUTES = 5  # minutes before expiry to trigger refresh

# Paths
DATA_DIR = "/data"
CONFIG_FILE = "config.json"
LOG_FILE = "gateway.log"
