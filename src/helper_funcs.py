from constants import *
from datetime import datetime, timezone
import os
import time

def epoch_to_local_date_string(epoch:int = 0):
	timestamped = datetime.utcfromtimestamp(epoch).replace(tzinfo=timezone.utc).astimezone(tz=None)
	return timestamped.strftime(DATETIME_FORMAT_LOCAL)

def epoch_to_utc_date_string(epoch:int = 0):
	timestamped = datetime.utcfromtimestamp(epoch).replace(tzinfo=timezone.utc).astimezone(tz=timezone.utc)
	return timestamped.strftime(DATETIME_FORMAT_UTC)

def normalize_path(path, replace_markers=False, save_name:str=OUTPUT_BANNERS['unknown_thing']):
	if len(path) < 1:
		return
	strip_path = os.path.normpath(path)
	if replace_markers:
		strip_path = RGX['timestamp_marker'].sub(str(int(time.time())), strip_path)
		clean_save_name = os.path.basename(save_name)
		clean_save_name = RGX['strip_hg_name'].sub('', clean_save_name)
		clean_save_name = RGX['strip_json_name'].sub('', clean_save_name)
		clean_save_name = clean_save_name.replace('.', '_')
		strip_path = RGX['save_name'].sub(clean_save_name, strip_path)
	return os.path.realpath(strip_path)
