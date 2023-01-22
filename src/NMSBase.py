import pprint

from constants import *
from helpers import *
from PartCounter import PartCounter
from GalacticAddress import GalacticAddress

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

