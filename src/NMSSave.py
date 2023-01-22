import json
import pprint

from constants import *
from helpers import *
from NMSBase import NMSBase
from PartCounter import PartCounter
from GalacticAddress import GalacticAddress

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

