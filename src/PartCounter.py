from constants import *
from helpers import *
import copy
from GalacticAddress import GalacticAddress

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

