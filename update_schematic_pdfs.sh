#!/bin/bash

for file in `find . -name "*.kicad_sch"`; do
    BASENAME="${file%.*}"
    if [ -f "$BASENAME.kicad_pro" ]; then
        kicad-cli sch export pdf $file -no $BASENAME.pdf
    fi
done
