#!/bin/bash

echo '```' > HELPTEXT.md
python3 ./NMSBasePartReporter.py -h >> HELPTEXT.md
echo '```' >> HELPTEXT.md

# At least at the beginning...
cp -pv HELPTEXT.md README.md