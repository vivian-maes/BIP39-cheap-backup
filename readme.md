# Sauvegarde de Clé BIP39 sur Carte 3D

Ce projet vous permet de générer une carte 3D (au format .scad) à partir d'une liste de mots BIP39. Une fois créée, cette carte peut être imprimée à l'aide d'une imprimante 3D pour une sauvegarde physique de votre clé.

## Considérations de Sécurité et Durabilité

Il est crucial de comprendre que bien que cette méthode de sauvegarde offre une certaine durabilité face aux usages courants, elle présente des limites intrinsèques en matière de résistance. En effet, étant donné que la carte est imprimée en plastique, elle n'est pas protégée contre des scénarios extrêmes tels que le feu, des températures élevées, ou d'autres catastrophes naturelles qui pourraient endommager ou fondre le plastique.

Sur le marché, il existe des solutions en titane conçues pour résister à de telles situations extrêmes. Ces solutions sont spécifiquement fabriquées pour offrir une protection maximale contre le feu, la corrosion, et d'autres conditions défavorables. Cependant, le coût de ces solutions en titane est souvent élevé, dépassant rapidement les 100 euros.

Pour les personnes possédant des portefeuilles cryptographiques de valeur élevée, il pourrait être judicieux d'investir dans de telles solutions pour garantir une protection optimale. Néanmoins, pour des portefeuilles de valeur moyenne ou pour ceux qui ne sont pas prêts à investir une somme considérable dans des solutions de sauvegarde haut de gamme, notre solution imprimée en 3D peut être suffisante. Elle offre une protection raisonnable contre l'usure quotidienne tout en étant économique.

Il est essentiel de peser le rapport coût-bénéfice en fonction de la valeur de votre portefeuille cryptographique et des risques que vous êtes prêt à prendre en matière de sauvegarde.

## Prérequis

Vous aurez besoin de Python pour exécuter ce projet.

## Installation et Dépendances

Tout d'abord, clonez ce dépôt :

```bash
git clone [url-du-dépôt]
cd [dossier-du-dépôt]
```

Ensuite, installez les dépendances Python nécessaires. Ce projet nécessite la bibliothèque `solid` pour générer des fichiers .scad :

```bash
pip install solidpy
```

## Fonctionnalités

1. **WordManager**: Cette classe est responsable de la lecture du fichier contenant les mots BIP39 et propose des méthodes pour obtenir des informations sur ces mots.
2. **CardDessing**: Cette classe crée le design de la carte 3D en fonction des mots fournis par `WordManager`. Elle permet également de sauvegarder le design sous forme de fichier .scad.

## Utilisation

1. Préparez un fichier texte contenant votre clé BIP39 (12, 18 ou 24 mots, un mot par ligne).
2. Exécutez l'application avec la commande suivante :

```bash
python main.py [chemin_vers_la_clé] [titre] [chemin_de_sauvegarde]
```

- `chemin_vers_la_clé`: Chemin vers le fichier texte contenant votre clé BIP39.
- `titre`: Titre de la carte.
- `chemin_de_sauvegarde`: Chemin du fichier où le design .scad sera sauvegardé.

## Exemple

Supposons que vous ayez un fichier nommé `maCle.txt` contenant votre clé BIP39, voici comment vous pourriez utiliser l'application :

```bash
python main.py maCle.txt "Ma Clé BIP39" carteDeSauvegarde.scad
```

⚠️ **Attention**: Le résultat final dépendra grandement de l'imprimante 3D utilisée ainsi que de la qualité d'impression. Assurez-vous de tester avec votre imprimante pour obtenir les meilleurs résultats.

## Contribution

Si vous avez des améliorations ou des suggestions pour ce projet, n'hésitez pas à ouvrir un ticket ou à soumettre une pull request.

---

J'espère que cela vous convient! Vous pouvez le personnaliser davantage si nécessaire.