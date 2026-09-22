# BIP39 Key 3D Card Backup

This project allows you to generate a 3D card (in .scad format) from a list of BIP39 words. Once created, this card can be printed using a 3D printer for a physical backup of your key.

## Security and Durability Considerations

It's crucial to understand that while this backup method offers some level of durability against common wear and tear, it has inherent limitations when it comes to resilience. Given that the card is printed in plastic, it is not protected against extreme scenarios such as fire, high temperatures, or other natural disasters that might damage or melt the plastic.

On the market, there are titanium solutions designed to withstand such extreme situations. These are specifically manufactured to offer maximum protection against fire, corrosion, and other harsh conditions. However, the cost of these titanium solutions is often high, quickly exceeding 100 euros.

For individuals with high-value cryptocurrency wallets, it might be wise to invest in such solutions to ensure optimal protection. However, for medium-value wallets or those not ready to invest a significant amount into high-end backup solutions, our 3D printed method might suffice. It offers reasonable protection against everyday wear and tear while being cost-effective.

It's essential to weigh the cost-benefit ratio based on the value of your cryptocurrency wallet and the risks you are willing to take in terms of backup.

## Prerequisites

You will need Python 3.10 or later to run this project (required by fonttools).

## Installation & Dependencies

First, clone this repository:

```bash
git clone [repository-url]
cd [repository-directory]
```

Next, create a virtual environment and install the dependencies. This project uses
SolidPython2 (imported as `solid2`) to generate .scad files:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The virtual environment is not optional on recent Python installs (Homebrew,
Debian/Ubuntu): a bare `pip install` there aborts with
`error: externally-managed-environment`.

## Card styles

`--mode engraved` (default) cuts the text into a single plate. `--mode contrast`
emits two plates to print in two filament colours: a base carrying the text in
relief, and a counter-plate pierced with the letter shapes that fills in around
them. Assembled, the top is flush and the text finally contrasts. Printing the
base alone and swapping filament mid-print gives the same contrast in one piece.

Glyph outlines are vectorised at generation time and embedded in the .scad, so a
card renders identically on any machine, with no font installed.

## Previewing before you print

`make_sample.sh` renders one PNG per generated .scad through `tools/preview.py`,
which rasterises the same outlines the .scad contains, with no OpenSCAD and no
third-party module. Proofread the card there before committing filament to it.

## STL and mesh checking

With `openscad` on the PATH, `make_sample.sh` also exports one .stl per .scad and
runs `tools/check_mesh.py` over them. STL files are not committed: they derive
from the .scad, weigh several MB and do not diff.

The mesh check is not a formality. A counter-plate encloses the middle of every
o, a, e, 8; without a bridge tying it to the rest of the plate it prints as a
loose speck, and neither the .scad nor a preview image reveals it — only counting
connected components does.

Install the engine with `brew install --cask openscad@snapshot`. The stable
`openscad` cask (2021.01) has been disabled since 2026-09-01: it no longer passes
macOS Gatekeeper.

## Functionality

1. **WordManager**: This class is responsible for reading the file containing the BIP39 words and provides methods to obtain information on these words.
2. **CardDessing**: This class creates the 3D card design based on the words provided by `WordManager`. It also allows you to save the design as a .scad file.

## Usage

1. Prepare a text file containing your BIP39 key (12, 15, 18, 21, or 24 words, one word per line). Blank lines and surrounding whitespace are ignored.
2. Run the application with the following command:

```bash
python main.py [key_path] [title] [save_path]
```

- `key_path`: Path to the text file containing your BIP39 key.
- `title`: Title of the card.
- `save_path`: Save file path where the .scad design will be saved.

## Example

Suppose you have a file named `myKey.txt` containing your BIP39 key, here's how you might use the application:

```bash
python main.py myKey.txt "My BIP39 Key" backupCard.scad
```

⚠️ **Warning**: The final result will greatly depend on the 3D printer used as well as the print quality. Make sure to test with your printer to achieve the best results.

## Contribution

If you have improvements or suggestions for this project, feel free to open an issue or submit a pull request.

---

I hope this meets your requirements! You can further customize it as needed.