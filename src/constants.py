import re

# Used for padding large numbers in sorted strings
ARBITRARY_NUMBER_SIZE = 16
THIS_VERSION='v1.0.0'
BASE_COMPUTER_OBJECTID = '^BASE_FLAG'
DATETIME_FORMAT_LOCAL = '%a %Y-%m-%d %H:%M:%S'
DATETIME_FORMAT_UTC = '%a %Y-%m-%d %H:%M:%S UTC'
DECIMAL_ROUNDINESS = 3
NMS_BASE_PART_LIMIT = 16000
NMS_STRAY_PART_LIMIT = 4000
NMS_UPLOAD_PART_LIMIT = 3000
OUTPUT_BANNERS = {
	'error' : 'ERROR: ',
	'freighter_base': '[Freighter Base]',
	'invalid_part': '[Invalid part]',
	'nil_value': '',
	'outside_base': '[Outside Base]',
	'unknown_thing': '[unknown]',
	'verbose' : '(Verbose) ',
	'warning' : 'WARNING: ',
}
PLAYER_BASE_TYPES = {
	'freighter': 'FreighterBase',
	'owned': 'HomePlanetBase',
}
REPLACEMENT_MARKERS = {
	'save_name': "[SAVE_NAME]",
	'timestamp': "[TIMESTAMP]",
}
RGX = {
	'save_name': re.compile(re.escape(REPLACEMENT_MARKERS['save_name']), re.IGNORECASE),
	'strip_hg_name': re.compile('\.hg', re.IGNORECASE),
	'strip_json_name': re.compile('\.json', re.IGNORECASE),
	'timestamp_marker': re.compile(re.escape(REPLACEMENT_MARKERS['timestamp']), re.IGNORECASE),
}
VALID_SORTS = [
	'name',
	'parts',
	'time',
]
