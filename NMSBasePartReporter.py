#!/usr/bin/python3

from collections import OrderedDict
import configargparse
import copy
from datetime import datetime, timezone
import json
import math
import pprint
import os
import re
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src'))
from constants import *
from GalacticAddress import GalacticAddress
from helper_funcs import *
import NMSDetails
from ProperHelpFormatter import ProperHelpFormatter

#-----------------------------------------------------------------------------------------------------------------------

class PartCounter:
	standins = {
		"Timestamp": 0,
		"ObjectID": OUTPUT_BANNERS['unknown_thing'],
		"GalacticAddress": None,
		"RegionSeed": None,
		"Position": [
			0,
			0,
			0,
		],
		"Up": [
			0,
			0,
			0,
		],
		"At": [
			0,
			0,
			0,
		]
	}

	def __init__(self, part_data:list, configuration):
		self.part_objects = part_data
		self.config = configuration
		self.out = self.config.out
		self.parts_clean = []
		self.part_counts = {}
		self.total_valid_count = 0
		self.total_invalid_count = 0
		self.invalid_objects = []
		self.populate_counts()

	def clean_part(self, part_data:dict, clean_invalid=False):
		valid = self.is_valid_part(part_data)
		if not valid and not clean_invalid:
			return
		cleaned = part_data.copy()
		cleaned['IsValid'] = valid
		if 'GalacticAddress' in cleaned and cleaned['GalacticAddress'] is not None:
			cleaned['GalacticAddress'] = GalacticAddress(cleaned['GalacticAddress'])
		attribs = self.standins.keys()
		for attr in attribs:
			if not attr in cleaned:
				cleaned[attr] = copy.deepcopy(self.standins[attr])
		if not 'ObjectID' in cleaned:
			cleaned['ObjectID'] = OUTPUT_BANNERS['invalid_part']
		return cleaned

	def find_parts_by_id(self, object_id:str):
		parts = []
		if len(object_id) < 1:
			return parts
		# We do this to include ones with valid IDs but are invalid parts.
		if object_id == OUTPUT_BANNERS['invalid_part']:
			return list(self.invalid_objects)
		for part in self.part_objects:
			cleaned = self.clean_part(part, clean_invalid=True)
			if cleaned['ObjectID'] == object_id:
				parts.append(cleaned)
		return parts

	def get_counts(self, part_sort:str="count", reversed:bool=True):
		counts = {}
		if type(part_sort) is str and part_sort.lower() == "name":
			keys = list(self.part_counts.keys())
			keys.sort(reverse=reversed)
			for key in keys:
				counts[key] = self.part_counts[key]
		else: # part_sort == "count" as a default
			counts = sorted(self.part_counts.items(), key=lambda x: x[1], reverse=reversed)
		return counts

	def get_invalid_parts(self):
		return list(self.invalid_objects)

	def get_sorted_parts(self, sort:str="name", reversed:bool=False):
		sorting = sort.lower()
		if sorting == "date" or sorting == "time":
			return sorted(self.parts_clean, key=lambda x: x['Timestamp'], reverse=reversed)
		# Default to by name + time
		return sorted(self.parts_clean, key=lambda x: x['ObjectID']+str(x['Timestamp']).rjust(ARBITRARY_NUMBER_SIZE, '0'), reverse=reversed)

	def get_total(self, include_invalid:bool=False):
		if include_invalid:
			return 0 + self.total_valid_count + self.get_total_invalid()
		else:
			return 0 + self.total_valid_count

	def get_total_invalid(self):
		return self.total_invalid_count

	def is_valid_part(self, obj):
		if not type(obj) is dict:
			return False
		attribs = self.standins.keys()
		for attr in attribs:
			if attr == "GalacticAddress":
				# In-base parts don't have an address.
				continue
			if attr == "RegionSeed":
				# In-base parts don't have a region.
				continue
			if not attr in obj:
				return False
		return True

	def populate_counts(self):
		if self.part_objects is None or len(self.part_objects) < 1:
			self.part_counts = {}
		else:
			for part in self.part_objects:
				cleaned = self.clean_part(part)
				if cleaned is None:
					cleaned = self.clean_part(part, clean_invalid=True)
					self.out.warn("Part \"{}\" is not a proper base part‽".format(cleaned['ObjectID']))
					self.invalid_objects.append(copy.deepcopy(part))
					self.total_invalid_count = self.total_invalid_count + 1
					continue
				self.total_valid_count = self.total_valid_count + 1
				self.parts_clean.append(cleaned)
				if cleaned['ObjectID'] in self.part_counts:
					self.part_counts[cleaned['ObjectID']] = self.part_counts[cleaned['ObjectID']] + 1
				else:
					self.part_counts[cleaned['ObjectID']] = 1
		return self.part_counts.copy()

	def report_all_parts(self):
		output = ""
		#sorted_objects = sorted(self.part_objects, key=lambda x: x['ObjectID'], reverse=False)
		sorted_objects = self.get_sorted_parts('time')

		for part in sorted_objects:
			timestamped = datetime.utcfromtimestamp(part['Timestamp']).replace(tzinfo=timezone.utc).astimezone(tz=None)
			if 'GalacticAddress' in part:
				output += "{} on {} near {} in {} ({}) at {}\n".format(part['ObjectID'],
					part['GalacticAddress'].hex(),
					GalacticAddress.position_to_latlong(part['Up']),
					nms_details.galaxy_names[part['GalacticAddress'].get_galaxy_number()],
					part['GalacticAddress'].get_galaxy_number(),
					epoch_to_local_date_string(part['Timestamp'])
				)
				#print("GA as raw {}".format(part['GalacticAddress'].raw()))
				#print("GA as dec {}".format(part['GalacticAddress'].dec()))
			else:
				output += "{} near {} at {\n".format(part['ObjectID'],
					GalacticAddress.position_to_latlong(part['Up']),
					timestamped.strftime('%a %Y-%m-%d %H:%M:%S [%z %Z]')
				)
				#print("GA as raw {}".format(part['GalacticAddress'].raw()))
				#print("GA as dec {}".format(part['GalacticAddress'].dec()))
		return output

	def report_part_counts(self, part_sort:str="count", reversed:bool=True):
		valid = self.get_counts(part_sort="name")
		invalid_count = self.get_total_invalid()
		total = self.get_total()
		output = ""
		out_format = "  {}: {}\n"
		# We can't do sorted() trickery well with these dicts.
		if part_sort == "name":
			part_keys = list(valid.keys())
			part_keys.sort(reverse=reversed)
			if invalid_count > 0:
				output += out_format.format(OUTPUT_BANNERS['invalid_part'], invalid_count)
			for part in part_keys:
				output += out_format.format(part, valid[part])
		else: # fall to by count
			parts_expanded = {}
			if invalid_count > 0:
				parts_expanded[str(invalid_count).rjust(ARBITRARY_NUMBER_SIZE, '0') + ' ** ' + OUTPUT_BANNERS['invalid_part']] = (OUTPUT_BANNERS['invalid_part'], invalid_count)
			for part in valid:
				parts_expanded[str(valid[part]).rjust(ARBITRARY_NUMBER_SIZE, '0') + ' ** ' + part] = (part, valid[part])
			ordered = list(parts_expanded.keys())
			ordered.sort(reverse=reversed)
			for part_key in ordered:
				output += out_format.format(parts_expanded[part_key][0], parts_expanded[part_key][1])
		return output.rstrip()

#-----------------------------------------------------------------------------------------------------------------------

class NMSBase:
	standins = {
		"BaseVersion": 0,
		"GalacticAddress": None,
		"Position": [
			0,
			0,
			0,
		],
		"Forward": [
			0,
			0,
			0,
		],
		"LastUpdateTimestamp": 0,
		"Owner": {
			"LID": "",
			"UID": "",
			"USN": "",
			"PTK": "",
			"TS": 0,
		},
		"Name": OUTPUT_BANNERS['unknown_thing'],
		"BaseType": {
			"PersistentBaseTypes": OUTPUT_BANNERS['unknown_thing'],
		},
		"LastEditedById": "",
		"LastEditedByUsername": "",
		"ScreenshotAt": [
			0.0,
			0.0,
			0.0
		],
		"ScreenshotPos": [
			0.0,
			0.0,
			0.0
		],
		"GameMode": {
			"PresetGameMode": OUTPUT_BANNERS['unknown_thing'],
		},
		"PlatformToken": "",
		"IsReported": False,
		"IsFeatured": False,
		"AutoPowerSetting": {
			"BaseAutoPowerSetting": OUTPUT_BANNERS['unknown_thing'],
		},
	}
	def __init__(self, base_data, configuration):
		self.base_object = {}
		self.base_name = None
		self.config = configuration
		self.galactic_address = None
		self.base_object = base_data
		self.part_counter = None
		if self.is_valid_base():
			if self.base_object['Name'] != "":
				self.base_name = base_data['Name']
			elif self.base_object['BaseType']['PersistentBaseTypes'] == PLAYER_BASE_TYPES['freighter']:
				self.base_name = "" + OUTPUT_BANNERS['freighter_base']
			else:
				self.base_name = "" + OUTPUT_BANNERS['unknown_thing']
			self.part_counter = PartCounter(self.base_object['Objects'], self.config)
			if 'GalacticAddress' in self.base_object and self.base_object['GalacticAddress'] is not None:
				self.galactic_address = GalacticAddress(self.base_object['GalacticAddress'])

	def __getattr__(self, attr):
		if attr in self.base_object:
			return self.base_object[attr]
		raise AttributeError("'NMSBase' object has no attribute '{}'".format(attr))

	def get_base_computer(self):
		parts = self.part_counter.find_parts_by_id(BASE_COMPUTER_OBJECTID)
		if len(parts) < 1:
			return
		return copy.deepcopy(parts[0])

	def get_name(self):
		return "" + self.base_name

	def get_total_parts(self, include_invalid:bool=False):
		return self.part_counter.get_total(include_invalid)

	def get_part_counts(self):
		return self.part_counter.get_counts()

	def get_total_invalid_parts(self):
		return self.part_counter.get_total_invalid()

	def is_player_base_type(self):
		return {True for i in PLAYER_BASE_TYPES if PLAYER_BASE_TYPES[i] == self.base_object["BaseType"]["PersistentBaseTypes"]} or False

	def is_valid_base(self):
		if not type(self.base_object) is dict:
			return False
		attribs = self.standins.keys()
		for attr in attribs:
			if not attr in self.base_object:
				return False
		return self.is_player_base_type()

#-----------------------------------------------------------------------------------------------------------------------

class NMSSave:
	save_file = None

	def __init__(self, configuration):
		self.config = configuration
		self.out = ConsoleOut(self.config)
		self.config.out = self.out

		self.base_percentages = {}
		self.outside_percentage = None
		self.total_bases = 0
		self.total_base_parts = 0

		self.fq_save_file_path = normalize_path(self.config.save_path)
		if self.fq_save_file_path is None or len(self.fq_save_file_path) < 1 or not os.path.exists(self.fq_save_file_path) or not os.path.isfile(self.fq_save_file_path):
			self.out.err('"{}" is not a valid NMS save file!'.format(self.config.save_path), fatality=1)

		self.out.v('Using save file "{}"...'.format(self.fq_save_file_path))
		if not self.save_file is None:
			close(self.save_file)
		try:
			self.save_file = open(self.fq_save_file_path)
		except Exception as fail_file:
			self.out.err('Fatal exception trying to open save file! {} - {}'.format(type(fail_file).__name__, str(fail_file)), fatality=2)

		try:
			self.save_data = json.load(self.save_file)
		except Exception as fail_json:
			self.out.err('Fatal exception trying to read save file as JSON! {} - {}'.format(type(fail_json).__name__, str(fail_json)), fatality=3)

		if not self.is_valid_save():
			self.out.err('Fatal exception trying to validate save file! Not valid NMS save data!', fatality=3)

		self.populate_bases()

		if self.config.bases:
			self.output_bases()

		if self.config.outside:
			self.populate_strays()
			self.get_outside_parts_percentage()
			self.output_outisde()

		self.out.v('Base reporting complete.')

		if len(self.config.csv) > 0:
			self.generate_bases_csv()

		if self.out.is_verbose and not self.out.is_warning and self.out.warning_count > 0:
			self.out.v("{}{} suppressed warning messages. Use the --warnings flag to show them or --help for more information.".format(OUTPUT_BANNERS['warning'], self.out.warning_count))

	def generate_bases_csv(self):
		fq_csv_path = normalize_path(self.config.csv, True, self.fq_save_file_path)
		if fq_csv_path is None or len(fq_csv_path) < 1:
			self.out.err('"{}" is not a valid name for CSV output!'.format(self.config.csv), fatality=10)
		self.out.v("Writing base information to CSV file \"{}\"...".format(fq_csv_path))
		if os.path.exists(fq_csv_path):
			self.out.warn("Overwriting destination file \"{}\"!".format(fq_csv_path))
		headers = [
			'Name',
			'Part Count,',
			'% of Part Limit (' + str(NMS_BASE_PART_LIMIT) + ')',
			'% of Used Parts',
			'Invalid Part Count,',
			'Game Mode',
			'Galactic Address',
			'Approximate Location',
			'Last Updated (local)',
			'Last Updated (UTC)',
			'Base Version',
			'Original Base Version',
			'Base Auto Power'
		]
		for idx in range(len(headers)):
			headers[idx] = headers[idx].replace('"', '\\"')
		final_out = ['"' + '", "'.join(headers) + '"']
		refs = self.get_refs_by(self.config.bs)
		for ref in refs:
			base = self.bases_by_name_and_time[ref]
			csv_out = []
			csv_out.append(base.base_name.replace('"', '\\"'))
			csv_out.append(str(base.get_total_parts(include_invalid=True)))
			csv_out.append(str(self.get_base_parts_percentage(base.get_total_parts(include_invalid=True))))
			csv_out.append(str(self.get_base_parts_percentage(base.get_total_parts(include_invalid=True), self.total_base_parts)))
			csv_out.append(str(base.get_total_invalid_parts()))
			csv_out.append(base.GameMode['PresetGameMode'])
			csv_out.append(base.galactic_address.hex())
			csv_out.append(str(GalacticAddress.position_to_latlong(base.Position)))
			csv_out.append(epoch_to_local_date_string(base.LastUpdateTimestamp))
			csv_out.append(epoch_to_utc_date_string(base.LastUpdateTimestamp))
			csv_out.append(str(base.BaseVersion))
			csv_out.append(str(base.OriginalBaseVersion))
			csv_out.append(base.AutoPowerSetting['BaseAutoPowerSetting'])
			final_out.append('"' + '", "'.join(csv_out) + '"')
		print("\n".join(final_out))
		#if not os.path.exists(self.fq_save_file_path) or not os.path.isfile(self.fq_save_file_path):
		#csv_file = open(self.full_path + '.' + file_type, 'w+')

	def get_base_ref(self, base:NMSBase, ref_type:str="name"):
		ref_type = ref_type.lower()
		template = "{} @ {} @ {}"
		if ref_type == "parts":
			return template.format(str(base.get_total_parts(True)).rjust(ARBITRARY_NUMBER_SIZE, '0'), base.base_name, base.galactic_address.hex())
		if ref_type == "time":
			return template.format(base.LastUpdateTimestamp, base.base_name, base.galactic_address.hex())
		# Default to by name, time, then addy.
		return template.format(base.base_name, base.LastUpdateTimestamp, base.galactic_address.hex())

	def get_base_parts_percentage(self, part_count, maximum:int=None):
		if type(maximum) is not int or maximum < 1:
			maximum = NMS_BASE_PART_LIMIT
		return round((part_count / maximum ) * 100, DECIMAL_ROUNDINESS)

	def get_outside_parts_percentage(self):
		if self.outside_percentage is None:
			self.outside_percentage = round((self.strays.get_total(include_invalid=True) / NMS_STRAY_PART_LIMIT ) * 100, DECIMAL_ROUNDINESS)
		return self.outside_percentage

	def get_refs_by(self, sort_by:str="name"):
		out_refs = []
		sort_by = sort_by.lower()
		ref_keys = []
		base_ref = None
		if sort_by == "parts":
			base_ref = self.base_refs_by_parts_and_name
		elif sort_by == "time":
			base_ref = self.base_refs_by_time_and_name
		else:
			base_ref = self.bases_by_name_and_time

		if base_ref is not None:
			ref_keys = list(base_ref.keys())
			ref_keys.sort()
			for ref in ref_keys:
				if sort_by == "name":
					out_refs.append(ref)
				else:
					out_refs.append(base_ref[ref])
		return out_refs

	def is_valid_save(self):
		if not 'GameKnowledgeData' in self.save_data:
			return False
		if not 'DiscoveryManagerData' in self.save_data:
			return False
		if not 'Version' in self.save_data:
			return False
		if not 'Platform' in self.save_data:
			return False
		if not 'PlayerStateData' in self.save_data:
			return False
		if not 'BaseBuildingObjects' in self.save_data['PlayerStateData']:
			return False
		if not 'PersistentPlayerBases' in self.save_data['PlayerStateData']:
			return False
		if not 'SpawnStateData' in self.save_data:
			return False
		return True

	def output_bases(self):
		if self.config.individual:
			self.out.report('Individual bases:')
			refs = self.get_refs_by(self.config.bs)
			for ref in refs:
				invalid_total = self.bases_by_name_and_time[ref].get_total_invalid_parts()
				invalid_string = ""
				self.out.report("  {}".format(self.bases_by_name_and_time[ref].get_name()))
				self.out.report("    Parts used: {}".format(self.bases_by_name_and_time[ref].get_total_parts()))
				if invalid_total > 0:
					invalid_string = self.out.report("    Invalid parts found: {}\n".format(invalid_total))
				self.out.report("    Percentage of all parts used: {}% of {}".format(self.get_base_parts_percentage(self.bases_by_name_and_time[ref].get_total_parts(include_invalid=True), self.total_base_parts),
					self.total_base_parts
				))
				self.out.report("    Allowed base parts used: {}% of {}".format(self.get_base_parts_percentage(self.bases_by_name_and_time[ref].get_total_parts(include_invalid=True)),
					NMS_BASE_PART_LIMIT
				))
		self.out.report("Total bases: {}".format(self.total_bases))
		self.out.report("Total parts: {}".format(self.total_base_parts))
		self.out.report("Allowed base parts used: {}% of {}".format(self.get_base_parts_percentage(self.total_base_parts), NMS_BASE_PART_LIMIT))

	def output_outisde(self):
		self.out.report("Parts outside of bases: {}".format(self.strays.get_total(include_invalid=True)))
		if self.config.totals:
			self.out.report(self.strays.report_part_counts())
		self.out.report('Allowed non-base parts used: {}% of {}'.format(self.get_outside_parts_percentage(), NMS_STRAY_PART_LIMIT))
		#self.out.report(self.strays.report_all_parts())

	def populate_bases(self):
		self.bases_by_name_and_time = {}
		self.base_refs_by_time_and_name = {}
		self.base_refs_by_parts_and_name = {}
		self.total_base_parts = 0
		for base in self.save_data['PlayerStateData']['PersistentPlayerBases']:
			nms_base = NMSBase(base_data=base, configuration=self.config)
			if not nms_base.is_valid_base():
				continue
			self.total_bases = self.total_bases + 1
			self.total_base_parts = self.total_base_parts + nms_base.get_total_parts(include_invalid=True)
			base_ref = self.get_base_ref(nms_base)
			self.bases_by_name_and_time[base_ref] = nms_base
			self.base_refs_by_time_and_name[self.get_base_ref(nms_base, "time")] = base_ref
			self.base_refs_by_parts_and_name[self.get_base_ref(nms_base, "parts")] = base_ref

	def populate_strays(self):
		self.strays = PartCounter(part_data=self.save_data['PlayerStateData']['BaseBuildingObjects'], configuration=self.config)

#-----------------------------------------------------------------------------------------------------------------------

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


########################################################################################################################
#
########################################################################################################################

if __name__ == '__main__':
	# Failsafe for old python
	if float(str(sys.version_info[0]) + '.' + str(sys.version_info[1])) < 3.5:
		print('-----PYTHON VERSION ERROR-----', file=sys.stderr)
		print('This program requires Python 3.5+. You may have it installed as "python3" and need to pass this script to it manually.',
			file=sys.stderr)
		exit(255)

	config_parser = configargparse.ArgParser(
		prog=os.path.basename(__file__),
		usage=None,
		description="A tool for reporting No Man's Sky base part usage.",
		formatter_class=ProperHelpFormatter,
		default_config_files=["part_report.ini"],
		epilog="",
		conflict_handler='error',
		add_help=True,
		add_config_file_help=False,
		add_env_var_help=False
	)
	config_parser.add('-b', '--bases',
		help='Examine bases. If neither --bases nor --outside are provided, both will be enabled as a default.',
		action='store_true',
	)
	config_parser.add('--bs', '--base-sort',
		help='Sort order to use for base reproting when showing individual bases (see --individual) or outputting CSV (--csv).'+
			' Valid sorts are "{}"'.format('", "'.join(VALID_SORTS[:-1]) + '", and "' + VALID_SORTS[-1]),
		default='name',
		metavar='SORT',
		type=str
	)
	config_parser.add('-c', '--csv',
		help='Write details about bases to a comma separated values file at CSV_DESTINATION.'+
			' You may include some template substitutions in your CSV file name.'+
			' Valid substitutions are [TIMESTAMP] (the current Unix Epoch as a timestamp) and [SAVE_NAME] (the name of the save file being examined with ".json" and ".hg" removed).'+
			' For example a CSV file name give as "bases_[SAVE_NAME]_[timestamp].csv" would be saved as something like "bases_save4_1674347708.csv".'
			' If the destination file exists, it will be overwritten.',
		default=configargparse.SUPPRESS,
		metavar='CSV_DESTINATION',
		type=str
	)
	config_parser.add('-i', '--individual',
		help='If examining bases, report totals for each individual base. Ignored if not using the --bases flag.',
		action='store_true',
	)
	config_parser.add('-o', '--outside', '--outside_bases',
		help='Only examine parts built outside of bases. If neither --bases nor --outside are provided, both will be enabled as a default.',
		action='store_true',
	)
	config_parser.add('-s', '--save', '--save_path',
		help='Path to NMS save file exported as JSON.',
		default='save.hg.json',
		metavar='FILE_PATH',
		type=str
	)
	config_parser.add('-q', '--quiet',
		help='Disable all output but errors.',
		action='store_true',
	)
	config_parser.add('-t', '--totals',
		help='List part totals by object ID in reports',
		action='store_true',
	)
	config_parser.add('-v', '--verbose',
		help='Enable verbose output to STDERR.',
		action='store_true',
	)
	config_parser.add('-w', '--warnings', '--show-warnings',
		help='Enable reporting warning messages to STDERR.',
		action='store_true',
	)

	configured = config_parser.parse_args()
	if not configured.bases or configured.outside:
		configured.bases = True
		configured.outside = True
	configured.save_path = configured.save

	if not hasattr(configured, 'csv') or configured.csv == configargparse.SUPPRESS:
		configured.csv = ''

	if not configured.bs in VALID_SORTS:
		configured.bs = 'name'

	our_save = NMSSave(configured)

	#save_file = open('launch_day.save2.hg.json')
	#save_data = json.load(save_file)
	#strays = PartCounter(save_data['PlayerStateData']['BaseBuildingObjects'], configured)
	#print("Total strays: {}".format(strays.get_total()))
	#print("Invalid strays: {}\n".format(strays.get_total_invalid()))
	#bases = []
	#bases_total_parts = 0
	#for base in save_data['PlayerStateData']['PersistentPlayerBases']:
	#	nms_base = NMSBase(base, configured)
	#	print("{}\n  Parts: {}\n  Invalid: {}".format(nms_base.get_name(), nms_base.get_total_parts(), nms_base.get_total_invalid_parts()))
	#	bases_total_parts = bases_total_parts + nms_base.get_total_parts() + nms_base.get_total_invalid_parts()
	#	#print(pprint.pformat(nms_base.get_part_counts()))
	#	bases.append(nms_base)
	#print("Total Bases: {}".format(len(bases)))
	#print("Total base parts: {}".format(bases_total_parts))


"""
PersistentPlayerBases
BaseBuildingObjects
TerrainEditData
TeleportEndpoints
ShipOwnership
FleetFrigates
SettlementStatesV2



ObjectID
"""
