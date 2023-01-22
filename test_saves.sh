#!/bin/bash

function do_testing () {
	echo -e "### Command: python3 NMSBasePartReporter.py -s ${*}\n"
	python3 NMSBasePartReporter.py -s $*
	echo -e "\n### Finished ${1}\n"
}

for FILE in ./saves/*.json; do
	do_testing ${FILE} $@
done

./generate_help.sh