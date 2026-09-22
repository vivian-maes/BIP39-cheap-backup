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
requirements.txt        dépendances (solidpython2, épinglé)
main.py                 CLI argparse : orchestre lecture + génération + sauvegarde
libs/word_manager.py    WordManager : lecture du fichier de mots, accès par index
libs/card_dessing.py    CardDessing : géométrie de la carte et rendu SolidPython
sample/keys.txt         clé de démonstration (24 mots, un par ligne)
sample/card.scad        sortie de référence générée par make_sample.sh
sample/card.png         rendu OpenSCAD de la carte
make_sample.sh          script de régénération de l'exemple
```

## Environnement et exécution

- Python 3.7 ou plus récent. Dépendance unique : `solidpython2` (module importé :
  `solid2`), déclarée dans `requirements.txt`.
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
git diff sample/card.scad
```

La sortie de `solid2` est déterministe (aucun en-tête daté) : à comportement
inchangé, `git diff` doit être **vide**. Toute différence est une modification
géométrique à assumer explicitement.

Pour un contrôle visuel, ouvrir le `.scad` dans OpenSCAD (le rendu dépend de la
police `Futura`, présente sur macOS mais pas partout).

## Conventions du code

- Méthodes en `camelCase` dans `WordManager`, en `snake_case` dans `CardDessing` :
  incohérent mais existant, suivre le style du fichier modifié.
- Docstrings en anglais, messages utilisateur et commentaires en français.
- `card_dessing.py` importe `solid2` et préfixe tous les appels : `solid2.<fonction>`.
  Pas d'import wildcard.
- Coquilles présentes dans l'API publique, **à ne pas renommer sans demande explicite**
  (cela casserait les appelants) :
  - la classe s'appelle `CardDessing` (pour « design ») ;
  - le paramètre s'appelle `tile` dans `main()` et `CardDessing.write_title()` (pour
    « title »), alors que l'argument CLI est bien `title` ;
  - le message d'erreur de `main.py` indique « 24, 18 ou mots » (le « 12 » manque).

## Points d'attention fonctionnels

- **`WordManager` n'utilise pas la wordlist BIP39 officielle.** Les index renvoyés par
  `getIndex`, `getByIndex` et `getBinaryIndex` sont des positions **dans le fichier
  fourni** (base 1), pas les index 1–2048 de la spécification. Il n'y a aucune
  validation des mots contre la liste officielle.
- `exist`, `getIndex` et `getBinaryIndex` ne sont pas utilisés par le flux de
  génération actuel.
- `main.py` n'accepte que 12, 18 ou 24 mots. La mise en page suppose
  `word_by_line = 3` et `rows = nombre_de_mots // 3`.
- Toute la géométrie est paramétrée par les constantes du `__init__` de `CardDessing`
  (marges, dimensions, police, tailles). Modifier ces valeurs plutôt que les calculs
  en aval, et vérifier que les mots les plus longs tiennent dans `max_size_word`.
- Le projet utilise **SolidPython2** (`solid2`). Ne pas revenir à `solidpython`
  1.x : ce paquet est figé depuis février 2022, épingle `PrettyTable==0.7.2` (2013)
  et importe `pkg_resources`, supprimé des setuptools récents.
- Contrairement à SolidPython 1.x, `solid2` n'ajoute pas le code source du module
  en commentaire à la fin du `.scad` généré.
