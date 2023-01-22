#!/bin/bash

function do_testing () {
	echo -e "### Testing ${1}\n"
	python3 NMSBasePartReporter.py -s $*
	echo -e "\n### Finished ${1}"
}

for FILE in ./saves/*.json; do
	do_testing ${FILE} $@
	echo $FILE;
done

#do_testing "busted_parts.save2.hg.json" $@
#do_testing "creative.save4.hg.json" $@

