#!/usr/bin/python3

import configargparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src'))
from constants import *
from NMSSave import NMSSave
from ProperHelpFormatter import ProperHelpFormatter

#-----------------------------------------------------------------------------------------------------------------------

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
		description='A tool for reporting No Man\'s Sky base part usage in various ways.'+
			' You can list totals for bases, parts outside of bases (like save beacons), and generate a CSV list of base stats.'+
			' Each of these has individual options like sorting that can be leveraged to customise your output.',
		formatter_class=ProperHelpFormatter,
		default_config_files=["part_report.ini"],
		epilog='(' + THIS_VERSION + ') Requires Python 3.5+',
		conflict_handler='error',
		add_help=True,
		add_config_file_help=False,
		add_env_var_help=False
	)
	config_parser.add('-b', '--bases',
		help='Examine bases. If neither --bases nor --outside are provided, both will be enabled as a default.',
		action='store_true',
		default=configargparse.SUPPRESS,
	)
	config_parser.add('--bs', '--base-sort',
		help='Sort order to use for base reproting when showing individual bases (see --individual) or outputting CSV (--csv).'+
			' Valid sorts are "{}"'.format('", "'.join(VALID_SORTS[:-1]) + '", and "' + VALID_SORTS[-1]),
		default='name',
		metavar='SORT',
		type=str
	)
	config_parser.add('-c', '--csv',
		help='Generate a Comma Separated Values (CSV) list of all base information.',
		action='store_true',
		default=configargparse.SUPPRESS,
	)
	config_parser.add('-i', '--individual',
		help='If examining bases, report totals for each individual base. Ignored if not using the --bases flag.',
		action='store_true',
		default=configargparse.SUPPRESS,
	)
	config_parser.add('-o', '--outside', '--outside_bases',
		help='Only examine parts built outside of bases. If neither --bases nor --outside are provided, both will be enabled as a default.',
		default=configargparse.SUPPRESS,
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
		default=configargparse.SUPPRESS,
		action='store_true',
	)
	config_parser.add('-t', '--totals',
		help='List part totals by object ID in reports',
		default=configargparse.SUPPRESS,
		action='store_true',
	)
	config_parser.add('-v', '--verbose',
		help='Enable verbose output to STDERR.',
		default=configargparse.SUPPRESS,
		action='store_true',
	)
	config_parser.add('-w', '--warnings', '--show-warnings',
		help='Enable reporting warning messages to STDERR.',
		default=configargparse.SUPPRESS,
		action='store_true',
	)

	configured = config_parser.parse_args()

	# Set these since their defaults are suppressed
	if not hasattr(configured, 'bases'):
		configured.bases = False
	if not hasattr(configured, 'csv'):
		configured.csv = False
	if not hasattr(configured, 'individual'):
		configured.individual = False
	if not hasattr(configured, 'outside'):
		configured.outside = False
	if not hasattr(configured, 'quiet'):
		configured.quiet = False
	if not hasattr(configured, 'totals'):
		configured.totals = False
	if not hasattr(configured, 'verbose'):
		configured.verbose = False
	if not hasattr(configured, 'warnings'):
		configured.warnings = False

	if not configured.bases and not configured.outside:
		configured.bases = True
		configured.outside = True

	if configured.csv:
		configured.bases = False
		configured.outside = False

	configured.save_path = configured.save

	if not configured.bs in VALID_SORTS:
		configured.bs = 'name'

	our_save = NMSSave(configured)

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
