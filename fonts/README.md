# Police embarquée

`JetBrainsMono-Bold.ttf` — JetBrains Mono, graisse Bold.

- Source : https://github.com/JetBrains/JetBrainsMono (`fonts/ttf/`)
- Licence : SIL Open Font License 1.1, texte intégral dans `OFL.txt`
- Récupérée le 2026-09-22

## Pourquoi cette police est dans le dépôt

Elle n'est pas désignée par son nom mais par son chemin, et ses contours sont
vectorisés en Python à la génération. OpenSCAD résoudrait un *nom* de police via
fontconfig au moment du rendu : la carte dépendrait alors des polices installées
sur la machine qui rend, et une substitution silencieuse rendrait une sauvegarde
de seed illisible. Embarquer le fichier est ce qui rend la carte reproductible.

## Pourquoi celle-ci

- **Chasse fixe** : l'avance est identique pour tous les caractères, donc le
  contrôle de largeur est exact et la mise en page ne dépend pas du mot tiré.
- **Graisse Bold** : mesuré au balayage, le fût de la Regular ne fait que
  0,315 mm à 3,5 mm de corps — moins qu'une buse de 0,4 mm. En relief, ce sont
  des parois libres inimprimables. La Bold monte à 0,437 mm, au-dessus du seuil,
  pour exactement la même avance : le changement de graisse ne déplace aucun mot.

## Licences

Le dépôt est sous GPLv3, la police sous OFL 1.1. Les deux coexistent par simple
agrégation : la police est une œuvre distincte livrée à côté du programme, pas
liée dedans. Le `.scad` généré contient les contours des glyphes, ce que l'OFL
autorise explicitement pour un document, sans que ce document tombe sous OFL.
La clause de nom réservé impose de ne pas redistribuer le fichier modifié sous
le nom « JetBrains Mono » : il est ici livré tel quel.
