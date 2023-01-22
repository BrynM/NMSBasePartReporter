import math

from constants import *

class GalacticAddress:
	def __init__(self, value):
		self.raw_value = value
		self.hex_value = self.normalize_to_hex(self.raw_value)
		self.address_parts = self.split_parts()

	def dec(self):
		return int(self.hex_value, 16)

	def get_galaxy_number(self):
		return int(self.address_parts['galaxy'], 16)

	def hex(self):
		return '' + self.hex_value

	def normalize_to_hex(self, odd_value):
		if type(odd_value) is str:
			return odd_value
		if type(odd_value) is int:
			hex_addy = hex(odd_value)
			hex_addy = hex_addy.upper()
			return str(hex_addy)

	@staticmethod
	def position_to_latlong(position:list):
		# Maybe https://steamcommunity.com/app/275850/discussions/0/2577697791651464012/
		# ! This kinda works. :/ !
		try:
			x = position[1]
			y = position[0]
			z = position[2]
			radius = math.sqrt((x*x)+(y*y)+(z*z))
			latitude = math.asin (y/radius) * 57.2957795
			temp_val = 2*(math.atan(z/(math.sqrt((x*x)+(z*z))-x))) * 57.2957795
			if (temp_val > 0):
				longitude = 180 - temp_val
			else:
				longitude = -180 - temp_val
			return (round(latitude, DECIMAL_ROUNDINESS), round(longitude, DECIMAL_ROUNDINESS))
		except Exception as math_fail:
			return (None, None)
		# https://www.reddit.com/r/NoMansSkyTheGame/comments/vs96cx/how_to_find_those_lost_save_points_signal/
		# NMS position vectors are y, z, x
		# ! This does not work. :/ !
		#try:
		#	if len(position) != 3:
		#		return (None, None)
		#	latitude = math.degrees(math.asin(position[1]))
		#	longitude = math.degrees(math.atan2(position[0], position[2]))
		#except Exception as math_fail:
		#	#print('Caught exception calculating lat/long for coordinates! {} - {}'.format(type(math_fail).__name__, str(math_fail)))
		#	latitude = None
		#	longitude = None
		#return (latitude, longitude)


	def raw(self):
		if type(self.raw_value) is str:
			return '' + self.raw_value
		if type(self.raw_value) is int:
			return 0 + self.raw_value
		if type(self.raw_value) is float:
			return 0.0 + self.raw_value
		if type(self.raw_value) is list:
			return list(self.raw_value)
		if type(self.raw_value) is dict:
			return self.raw_value.copy()
		return self.raw_value

	def split_parts(self):
		'''
		https://nomanssky.fandom.com/wiki/Universal_Address
		[??][P][SSS][GG][YY][ZZZ][XXX]
		(? = Unknown / P = Planet Index / S = Star System Index /G = Galaxy / Y = Height / Z = Width / X = Length)
			0x40430000F1D907
			0x - unused
			4 - planet
			043 - system
			00 - galaxy hex
			00 - y hex
			F1D - z hex
			907 - x hex
		'''
		return {
			"planet": ''+ self.hex_value[2:3],
			"system": ''+ self.hex_value[3:6],
			"galaxy": ''+ self.hex_value[6:8],
			"y": ''+ self.hex_value[8:10],
			"z": ''+ self.hex_value[10:13],
			"x": ''+ self.hex_value[13:16],
		}

	#def voxel(self):
	#	# https://www.reddit.com/r/NoMansSkyTheGame/comments/uelzb6/a_short_tutorial_on_converting_galactic_addresses/
	#	# int(hex_val, 16)

