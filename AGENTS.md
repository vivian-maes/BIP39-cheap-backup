# AGENTS.md

Instructions pour les agents travaillant sur ce dépôt.

## Objectif du projet

Générer une carte 3D (fichier OpenSCAD `.scad`) à partir d'une liste de mots BIP39,
afin d'imprimer une sauvegarde physique d'une seed de portefeuille cryptographique.
Le texte est **gravé en creux** (soustraction booléenne) dans une plaque au format
carte bancaire (85 × 55 × 1 mm).

Licence : GPL v3. Documentation utilisateur : `readme.md` (EN) et `readme.fr.md` (FR).

## ⚠️ Règle de sécurité prioritaire

Ce code manipule des **seeds BIP39**, c'est-à-dire un accès total aux fonds.

- Ne jamais afficher, logger, copier hors du dépôt, ni committer le contenu d'un
  fichier de clé fourni par l'utilisateur.
- Ne jamais envoyer un fichier de clé ou un `.scad` généré vers un service externe
  (API, upload, pastebin, recherche web…).
- `sample/keys.txt` est une clé de démonstration publique : elle est versionnée
  volontairement et ne doit **jamais** servir de vraie sauvegarde. Utiliser
  uniquement ce fichier pour les tests ; ne jamais en créer un autre avec des mots
  réels.
- Les sorties de test vont dans `sample/` ou un répertoire temporaire, pas ailleurs.

## Structure

```
requirements.txt          dépendances (solidpython2, fonttools — épinglées)
main.py                   CLI argparse : --mode engraved|contrast
libs/word_manager.py      WordManager : lecture du fichier de mots, accès par index
libs/glyph_outline.py     FontOutliner : texte -> contours en mm (fontTools)
libs/card_dessing.py      CardDessing : géométrie de la carte et rendu SolidPython
tools/preview.py          rendu PNG des .scad, sans OpenSCAD ni dépendance
fonts/                    police embarquée + sa licence, voir fonts/README.md
sample/keys.txt           clé de démonstration (24 mots, un par ligne)
sample/card.scad          référence, mode gravé
sample/card_contrast.*.scad  références, mode contrasté (single, base, counter)
sample/*.png              un aperçu par .scad, régénéré par make_sample.sh
make_sample.sh            script de régénération des exemples
```

## Environnement et exécution

- **Python 3.10 ou plus récent** — plancher imposé par `fonttools`. Dépendances :
  `solidpython2` (importé `solid2`) et `fonttools`, épinglées dans `requirements.txt`.
- Installation **dans un venv** (`venv/`, `.venv/` et `env/` sont déjà dans
  `.gitignore`) :
  `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
  Le venv n'est pas facultatif : `pip install` direct échoue en
  `externally-managed-environment` sur Python Homebrew/Debian (PEP 668).
- `make_sample.sh` appelle `python3` : il faut donc que le venv soit **activé**,
  sinon `ModuleNotFoundError: No module named 'solid2'`.
- Pas de packaging, pas de venv versionné dans le dépôt.

Lancer :

```bash
python3 main.py <key_path> "<titre>" <save_path>
./make_sample.sh          # régénère sample/card.scad
```

## Vérifier une modification

Il n'y a ni tests, ni linter, ni CI. La vérification se fait par comparaison de la
sortie de référence :

```bash
./make_sample.sh
git diff sample/
```

La sortie est déterministe : pas d'en-tête daté, contours vectorisés par
subdivision déterministe, coordonnées arrondies à `COORD_DECIMALS`. À
comportement inchangé, `git diff` doit être **vide** sur les trois `.scad`.
Toute différence est une modification géométrique à assumer explicitement.

Pour un contrôle visuel, `make_sample.sh` produit **un PNG par `.scad`** via
`tools/preview.py`, qui rastérise les mêmes contours avec la même règle pair-impair
qu'OpenSCAD — un aperçu aux contreformes creuses prouve donc que le `.scad` les a
creuses. C'est ce rendu qui a révélé que les ponts transformaient le `0` en `U`.
Les images étant régénérées avec les `.scad`, elles ne peuvent plus se périmer.

On peut aussi ouvrir le `.scad` dans OpenSCAD. Le rendu ne dépend plus
d'aucune police installée : les contours sont dans le fichier.

**Version d'OpenSCAD** : la dernière version *stable* est 2021.01 ; le
développement se poursuit en nightly, où le backend Manifold est devenu le défaut.
Aucune n'est installée sur la machine de développement, donc **aucune version de
validation n'est encore consignée ici** — à renseigner après le premier contrôle
visuel réel. La vectorisation des contours réduit fortement la sensibilité à la
version, puisque le rendu de `text()`, qui variait selon la pile de polices du
moteur, n'intervient plus.

## Conventions du code

- Méthodes en `camelCase` dans `WordManager`, en `snake_case` dans `CardDessing` :
  incohérent mais existant, suivre le style du fichier modifié.
- Docstrings en anglais, messages utilisateur et commentaires en français.
- `card_dessing.py` importe `solid2` et préfixe tous les appels : `solid2.<fonction>`.
  Pas d'import wildcard.
- `glyph_outline.py` ne connaît ni les cartes ni OpenSCAD : il ne fait que « texte
  vers contours ». Ne rien y importer de `solid2`.
- Indentation : 2 espaces dans `card_dessing.py`, 4 ailleurs. Suivre le fichier.
- Coquilles présentes dans l'API publique, **à ne pas renommer sans demande explicite**
  (cela casserait les appelants) :
  - la classe s'appelle `CardDessing` (pour « design ») ;
  - le paramètre s'appelle `tile` dans `main()` (pour « title »), alors que
    l'argument CLI est bien `title`.

## Points d'attention fonctionnels

- **`WordManager` n'utilise pas la wordlist BIP39 officielle.** Les index renvoyés par
  `getIndex`, `getByIndex` et `getBinaryIndex` sont des positions **dans le fichier
  fourni** (base 1), pas les index 1–2048 de la spécification. Il n'y a aucune
  validation des mots contre la liste officielle.
- `getBinaryIndex` renvoie un champ BIP39 de 11 bits en base 0 (`format(i - 1, '011b')`),
  et `None` au-delà de la 2048ᵉ position. `exist`, `getIndex`, `getIndices` et
  `getBinaryIndex` ne sont pas utilisés par le flux de génération actuel.
- `main.py` accepte les cinq longueurs BIP39 (`VALID_WORD_COUNTS` = 12, 15, 18, 21, 24).
  La mise en page suppose `word_by_line = 3` et arrondit au supérieur
  (`rows = ceil(n / 3)`) : sans cela, un compte non multiple de 3 plaçait les derniers
  mots en `y` négatif, hors carte et sans erreur.
- **Le débordement de colonne est contrôlé sur des largeurs mesurées.** Les contours
  étant vectorisés côté Python, `FontOutliner.text_width()` donne la largeur exacte ;
  `_fit_base_font_size()` réduit la police en conséquence. La réduction est normale et
  silencieuse ; seul un résultat sous `MIN_LEGIBLE_FONT_SIZE` déclenche un avertissement.
- Toute la géométrie est paramétrée par les constantes du `__init__` de `CardDessing`
  (marges, dimensions, police, tailles). Modifier ces valeurs plutôt que les calculs
  en aval.
- `row_height = top_text_zone / rows` n'utilise que `rows - 1` intervalles : une rangée
  de la zone réservée reste vide et le bloc de texte est plus bas que les constantes ne
  le laissent croire. Connu, non corrigé — le rectifier déplacerait le texte sur toutes
  les cartes déjà imprimées.
- Le projet utilise **SolidPython2** (`solid2`). Ne pas revenir à `solidpython`
  1.x : ce paquet est figé depuis février 2022, épingle `PrettyTable==0.7.2` (2013)
  et importe `pkg_resources`, supprimé des setuptools récents.
- Contrairement à SolidPython 1.x, `solid2` n'ajoute pas le code source du module
  en commentaire à la fin du `.scad` généré.

## Contours vectorisés

- **Le `.scad` ne contient plus aucun `font = `.** `text()` laissait le *rendu*
  résoudre la police via fontconfig : la même carte devenait illisible sur une
  machine dépourvue de la police. Les glyphes sont donc vectorisés à la génération
  et émis en `polygon(points, paths)`, les contreformes (`o`, `a`, `e`, `8`) étant
  traitées par la règle pair-impair d'OpenSCAD.
- Conséquence : les mots deviennent des milliers de coordonnées et le fichier passe
  de ~7 ko à ~120 ko. L'auditabilité est restaurée par le bloc d'en-tête émis via
  `file_header=`, qui liste chaque mot et sa position. **Ce bloc n'utilise que des
  commentaires `//`** et passe toute chaîne par `_sanitize()` : le titre vient de
  `argv`, et un saut de ligne y injecterait du code OpenSCAD arbitraire.
- `font_size` désigne le **cadratin**, convention typographique usuelle. OpenSCAD
  dimensionnait `text()` sur l'ascendante : à valeur égale, le texte est donc un peu
  plus petit qu'avant.

## Carte contrastée (`--mode contrast`)

- Deux pièces à imprimer dans deux couleurs : `base` (plaque + texte en relief) et
  `counter` (contre-plaque ajourée qui comble autour). Assemblées, le dessus est plan.
- La pièce `base` seule est aussi la variante monobloc : imprimer et changer de
  filament à `filament_change_height()`.
- **Les ponts ne sont pas décoratifs.** Sans eux, chaque contreforme de la
  contre-plaque est un îlot de plastique enfermé par sa lettre et rattaché à rien :
  90 spécules libres sur la carte d'exemple. `counter_bridges()` relie chacune vers
  le bord le plus proche du glyphe, d'où l'aspect pochoir. Les deux pièces doivent
  s'accorder : la base retire `offset(clearance)(ponts)`, la contre-plaque les ajoute.
- `clearance` (0,15 mm par côté) est **spécifique à l'imprimante** et ne peut pas être
  validé depuis le `.scad` : une impression d'essai est indispensable.
- La police embarquée est en graisse **Bold** pour une raison mesurée, pas esthétique :
  le fût de la Regular ne fait que 0,315 mm à 3,5 mm de corps, sous une buse de
  0,4 mm. En relief ce sont des parois libres inimprimables. Voir `fonts/README.md`.
