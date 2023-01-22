```
Usage:
  NMSBasePartReporter.py [-h] [-b] [--bs SORT] [-c] [-i] [-o]
                                [-s FILE_PATH] [-q] [-t] [-v] [-w]

Description:
  A tool for reporting No Man's Sky base part usage in various ways. You can
list totals for bases, parts outside of bases (like save beacons), and
generate a CSV list of base stats. Each of these has individual options like
sorting that can be leveraged to customise your output.

Optional arguments:
  --bs SORT, --base-sort SORT
                        Sort order to use for base reproting when showing
                        individual bases (see --individual) or outputting CSV
                        (--csv). Valid sorts are "name", "parts", and "time"
                        (Default: "name")
  -b, --bases
                        Examine bases. If neither --bases nor --outside are
                        provided, both will be enabled as a default.
  -c, --csv
                        Generate a Comma Separated Values (CSV) list of all
                        base information.
  -h, --help
                        Show this help message and exit
  -i, --individual
                        If examining bases, report totals for each individual
                        base. Ignored if not using the --bases flag.
  -o, --outside, --outside_bases
                        Only examine parts built outside of bases. If neither
                        --bases nor --outside are provided, both will be
                        enabled as a default.
  -q, --quiet
                        Disable all output but errors.
  -s FILE_PATH, --save FILE_PATH, --save_path FILE_PATH
                        Path to NMS save file exported as JSON. (Default:
                        "save.hg.json")
  -t, --totals
                        List part totals by object ID in reports
  -v, --verbose
                        Enable verbose output to STDERR.
  -w, --warnings, --show-warnings
                        Enable reporting warning messages to STDERR.

Version:
  v1.0.1; Requires Python 3.5+

Copyright:
  2023 Bryn Mosher - Released MIT License
```
