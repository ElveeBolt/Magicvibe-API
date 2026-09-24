from importlib.metadata import metadata, version

DISTRIBUTION_NAME = "magicvibe"

_distribution = metadata(DISTRIBUTION_NAME)

APP_VERSION = version(DISTRIBUTION_NAME)
APP_DESCRIPTION = _distribution.get("Summary", "")

APP_TITLE = "MagicVibe API"
