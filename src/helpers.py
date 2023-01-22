from constants import *
from datetime import datetime, timezone
import os
import sys
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

class ConsoleOut:
	def __init__(self, configuration):
		self.config = configuration
		self.is_quiet = hasattr(configuration, 'quiet') and configuration.quiet
		self.is_verbose = not self.is_quiet and hasattr(configuration, 'verbose') and configuration.verbose
		self.is_warning = not self.is_quiet and hasattr(configuration, 'warnings') and configuration.warnings
		self.warning_count = 0

	def err(self, *args, fatality:int=0, **kwargs):
		largs = list(args)
		if type(largs[0]) is str:
			largs[0] = OUTPUT_BANNERS['error'] + largs[0]
		kwargs['file'] = sys.stderr
		print(*largs, **kwargs)
		if fatality > 0:
			exit(fatality)

	def put(self, *args, **kwargs):
		if self.is_quiet:
			return
		print(*args, **kwargs)

	def report(self, *args, **kwargs):
		if not self.is_quiet:
			print(*args, **kwargs)

	def v(self, *args, **kwargs):
		self.verbose(*args, **kwargs)

	def verbose(self, *args, **kwargs):
		if not self.is_verbose:
			return
		largs = list(args)
		if type(largs[0]) is str:
			largs[0] = OUTPUT_BANNERS['verbose'] + largs[0]
		kwargs['file'] = sys.stderr
		print(*largs, **kwargs)

	def warn(self, *args, **kwargs):
		self.warning_count = self.warning_count + 1
		if not self.is_warning:
			return
		largs = list(args)
		if type(largs[0]) is str:
			largs[0] = OUTPUT_BANNERS['warning'] + largs[0]
		kwargs['file'] = sys.stderr
		print(*largs, **kwargs)
