#!/usr/bin/env bash
set -euo pipefail

clear
python3 main.py sample/keys.txt "Example de carte" sample/card.scad
python3 main.py sample/keys.txt "Example de carte" sample/card_contrast.scad --mode contrast

# Un PNG par .scad : une image périmée est exactement le piège dans lequel
# sample/card.png était tombé.
python3 tools/preview.py sample/keys.txt "Example de carte" sample
