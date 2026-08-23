"""Constants for Eshtaya Entity Manager."""

from __future__ import annotations

DOMAIN = "eshtaya_smart_control"
WS_PREFIX = f"{DOMAIN}/entity"
NAME = "Eshtaya Smart Control · Entity Control"
VERSION = "1.0.0"

PANEL_URL_PATH = "eshtaya-entity-manager"
PANEL_WEB_COMPONENT = "eshtaya-entity-manager-panel"
PANEL_TITLE = "Entity Manager"
PANEL_ICON = "mdi:account-eye-outline"
STATIC_URL = f"/{DOMAIN}/frontend"

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.entity_control"
HIDDEN_FILE = "hidden_entities.yaml"
PUBLIC_HIDDEN_FILE = "www/hidden_entities.yaml"
BACKUP_FILE = "hidden_entities.yaml.pre_eshtaya_backup"
PUBLIC_BACKUP_FILE = "www/hidden_entities.yaml.pre_eshtaya_backup"
RULES_BACKUP_FILE = "eshtaya_smart_control_entity_rules_backup.json"

DEFAULT_DISABLED_DOMAINS = {
    "sensor",
    "binary_sensor",
    "button",
    "number",
    "select",
    "update",
    "event",
    "image",
    "camera",
}

DEFAULT_EXCLUDED_ENTITY_CATEGORIES = ["diagnostic", "config"]
DEFAULT_EXCLUDED_NAME_KEYWORDS = ["backlight", "child_lock", "browser_mod"]

RULE_INHERIT = "inherit"
RULE_ALLOW = "allow"
RULE_EXCLUDE = "exclude"
RULE_VALUES = {RULE_INHERIT, RULE_ALLOW, RULE_EXCLUDE}
