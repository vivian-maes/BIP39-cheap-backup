#!/usr/bin/env bash
set -euo pipefail

clear
python3 main.py sample/keys.txt "Example de carte" sample/card.scad
python3 main.py sample/keys.txt "Example de carte" sample/card_contrast.scad --mode contrast

# Un PNG par .scad : une image périmée est exactement le piège dans lequel
# sample/card.png était tombé.
python3 tools/preview.py sample/keys.txt "Example de carte" sample

# Les STL sont dérivés et ne sont pas versionnés (voir .gitignore). OpenSCAD est
# le seul à évaluer les booléens ; sans lui on prévient et on passe, plutôt que
# d'échouer sur une machine qui ne fait que régénérer les .scad.
if command -v openscad >/dev/null 2>&1; then
  for scad in sample/*.scad; do
    openscad -o "${scad%.scad}.stl" "$scad" >/dev/null 2>&1
    echo "Save mesh to ${scad%.scad}.stl"
  done
  # Le seul contrôle qui révèle un îlot détaché : ni le .scad ni l'aperçu ne le
  # montrent.
  python3 tools/check_mesh.py sample/*.stl
else
  echo "openscad introuvable : STL non générés."
  echo "  brew install --cask openscad@snapshot"
fi
