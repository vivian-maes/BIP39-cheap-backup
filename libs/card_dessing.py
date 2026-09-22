import hashlib
import math
import os
import warnings

import solid2

from libs.glyph_outline import COORD_DECIMALS, FontOutliner

# Police embarquée dans le dépôt. Elle est vendorée et non désignée par son nom,
# car OpenSCAD résoudrait un nom via fontconfig au moment du rendu : la carte
# dépendrait alors des polices installées sur la machine qui rend, ce qui est
# inacceptable pour une sauvegarde de seed.
DEFAULT_FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'fonts', 'JetBrainsMono-Bold.ttf')

# En deçà, les glyphes gravés deviennent douteux à l'impression FDM.
MIN_LEGIBLE_FONT_SIZE = 2.0


def _sanitize(text):
  """
  Make a string safe to interpolate into a `//` comment line.

  The title comes straight from argv: a newline in it would end the comment and
  inject arbitrary OpenSCAD into the generated file. Only `//` comments are used
  precisely so that a `*/` in a title cannot close a block comment either.
  """
  return ''.join(' ' if ord(c) < 32 or ord(c) == 127 else c for c in text)


class CardDessing:
  def __init__(self, key_word, title, font_path=DEFAULT_FONT_PATH, font_number=0):
    self.key_word   = key_word
    # Nettoyé dès l'entrée : un caractère de contrôle n'a pas de glyphe (donc
    # échec à la vectorisation) et, dans l'en-tête, un saut de ligne fermerait le
    # commentaire et injecterait du code OpenSCAD arbitraire.
    self.title      = _sanitize(title)

    self.margin       = 2
    self.word_margin  = 1

    self.card_height  = 1.0
    self.card_width   = 55.0
    self.card_length  = 85.0

    self.font_path    = font_path
    self.text_height  = ( self.card_height / 2 ) + 0.1
    self.text_z_pos   = self.card_height - (self.card_height / 2)

    # Carte contrastée : la base porte le texte en relief, la contre-plaque vient
    # combler autour. Le jeu est appliqué par côté sur les perçages.
    self.base_height    = self.card_height
    self.relief_height  = 0.6
    self.clearance      = 0.15
    # Largeur des ponts rattachant les contreformes au reste de la contre-plaque.
    # 1,5 × une buse de 0,4 mm : en deçà, le pont lui-même ne s'imprime pas.
    self.bridge_width   = 0.6

    self.base_font_size    = 3.5
    self.title_font_size   = self.base_font_size * 1.2

    self.outliner = FontOutliner(font_path, font_number=font_number)

    word_count = self.key_word.getWordCount()
    if word_count <= 0:
      raise ValueError("La liste de mots est vide : impossible de dessiner une carte.")

    self.word_by_line   = 3
    # ceil et non // : avec un nombre de mots non multiple de word_by_line, les
    # derniers mots tombaient sur une rangée d'indice 0, donc en y négatif, et
    # étaient gravés hors de la carte sans la moindre erreur.
    self.rows           = math.ceil(word_count / self.word_by_line)

    row_lost_space      = (self.margin * 2) + ((self.word_by_line - 1) * self.word_margin)
    self.max_size_word  = (self.card_length - row_lost_space) / self.word_by_line

    self.top_text_zone  = self.card_width - (self.margin * 2.5 ) - self.title_font_size
    self.row_height     = self.top_text_zone / self.rows

    self._fit_base_font_size()

    # Rempli par make_card(). Déclaré ici pour que save() puisse diagnostiquer un
    # appel hors séquence au lieu de lever un AttributeError opaque.
    self.data = None

  def _word_label(self, word_index):
    """
    Build the engraved label for a word: its 2-digit position, then the word.
    """
    return f"{str(word_index).zfill(2)} {self.key_word.getByIndex(word_index)}"

  def _fit_base_font_size(self):
    """
    Shrink base_font_size until the longest label fits inside its column.

    max_size_word was computed but never enforced: a long word simply overran into
    the neighbouring column or off the card edge, silently, yielding an illegible
    seed backup.

    Widths are now measured against the real font outlines rather than estimated
    from a per-character ratio, so the fit is exact. Shrinking to fit is normal
    and stays quiet; only a result below MIN_LEGIBLE_FONT_SIZE warrants a warning.
    """
    labels = [self._word_label(i)
              for i in range(1, self.key_word.getWordCount() + 1)]
    widest = max(labels, key=lambda s: self.outliner.text_width(s, 1.0))
    width = self.outliner.text_width(widest, self.base_font_size)
    if width <= self.max_size_word:
      return

    fitted = self.base_font_size * (self.max_size_word / width)
    if fitted < MIN_LEGIBLE_FONT_SIZE:
      warnings.warn(
          f"« {widest} » impose de réduire la police à {fitted:.2f} mm pour tenir "
          f"dans {self.max_size_word:.1f} mm, sous le seuil de lisibilité de "
          f"{MIN_LEGIBLE_FONT_SIZE:.1f} mm : la carte risque d'être illisible.",
          stacklevel=3)
    self.base_font_size = fitted
    self.title_font_size = self.base_font_size * 1.2

  def layout(self):
    """
    Compute where every label sits on the card.

    Shared by the geometry and by the audit header, so the two can never disagree.

    Returns:
        list[tuple[int, str, float, float]]: (index, label, x, y) per word, with x
        and y in millimetres from the bottom-left corner, on the text baseline.
    """
    placed = []
    for word_index in range(1, self.key_word.getWordCount() + 1):
      row = (word_index -1) // self.word_by_line
      row = self.rows - row
      word = word_index - ((self.rows - row) * self.word_by_line)

      x = self.margin + ((word - 1) *  self.word_margin) + ((word - 1) *  self.max_size_word)
      y = ((row - 1) * self.row_height) + self.margin

      placed.append((word_index, self._word_label(word_index),
                     round(x, COORD_DECIMALS), round(y, COORD_DECIMALS)))
    return placed

  # -- géométrie 2D -------------------------------------------------------

  def _text_polygon(self, text, font_size):
    """
    Turn a string into a single OpenSCAD polygon.

    Every contour of every glyph goes into one points list, with `paths` carrying
    the index ranges. Counters (the inside of o, a, e, 8) are separate contours
    and OpenSCAD's even-odd rule renders them as holes.
    """
    contours = self.outliner.contours(text, font_size)
    points = []
    paths = []
    for contour in contours:
      start = len(points)
      points.extend(contour)
      paths.append(list(range(start, len(points))))
    if not points:
      return None
    return solid2.polygon(points=points, paths=paths)

  def _title_2d(self):
    """
    The title outline, horizontally centred on the card.

    text() did the centring with halign='center'; with explicit polygons the
    offset has to be computed from the measured width.
    """
    width = self.outliner.text_width(self.title, self.title_font_size)
    x = round((self.card_length / 2) - (width / 2), COORD_DECIMALS)
    y = round(self.card_width - self.margin - self.title_font_size, COORD_DECIMALS)
    polygon = self._text_polygon(self.title, self.title_font_size)
    if polygon is None:
      return None
    return solid2.translate([x, y])(polygon)

  def _text_2d(self):
    """
    The union of every engraved shape on the card: title plus all words.

    This is the single source of geometry for the three card variants.
    """
    parts = []
    title = self._title_2d()
    if title is not None:
      parts.append(title)
    for _, label, x, y in self.layout():
      polygon = self._text_polygon(label, self.base_font_size)
      if polygon is not None:
        parts.append(solid2.translate([x, y])(polygon))
    return solid2.union()(*parts)

  def _plate_2d(self):
    """
    The card outline.
    """
    return solid2.square([self.card_length, self.card_width])

  def _bridges_2d(self):
    """
    The union of every counter bridge, placed on the card.

    Only the contrast card needs these. On the engraved card a counter is simply
    uncut material, still attached to the plate; on the counter-plate it is an
    enclosed island attached to nothing.

    Returns:
        A 2D solid2 object, or None when no glyph on the card has a counter.
    """
    bars = []

    def collect(text, font_size, dx, dy):
      for x0, y0, x1, y1 in self.outliner.counter_bridges(
          text, font_size, self.bridge_width):
        bars.append(solid2.translate(
            [round(dx + x0, COORD_DECIMALS), round(dy + y0, COORD_DECIMALS)])(
                solid2.square([round(x1 - x0, COORD_DECIMALS),
                               round(y1 - y0, COORD_DECIMALS)])))

    title_width = self.outliner.text_width(self.title, self.title_font_size)
    collect(self.title, self.title_font_size,
            round((self.card_length / 2) - (title_width / 2), COORD_DECIMALS),
            round(self.card_width - self.margin - self.title_font_size, COORD_DECIMALS))
    for _, label, x, y in self.layout():
      collect(label, self.base_font_size, x, y)

    if not bars:
      return None
    return solid2.union()(*bars)

  def count_counters(self):
    """
    How many enclosed counters the card contains.

    Reported to the user because it is the number of loose islands the
    counter-plate would shed if bridging were ever disabled.
    """
    total = len(self.outliner.counter_bridges(
        self.title, self.title_font_size, self.bridge_width))
    for _, label, _, _ in self.layout():
      total += len(self.outliner.counter_bridges(
          label, self.base_font_size, self.bridge_width))
    return total

  # -- cartes -------------------------------------------------------------

  def make_card(self):
    """
    Build the engraved card: text cut into the plate.

    This method does not take any parameters.

    This method does not return anything.
    """
    self.data = self.make_card_base()
    self.data -= solid2.translate([0, 0, self.text_z_pos])(
        solid2.linear_extrude(height=self.text_height, convexity=4)(self._text_2d()))

  def make_card_base(self):
    """
    Generates the base of a card.

    Returns:
        cube: A solid object representing the base of the card.
    """
    cube = solid2.cube([self.card_length, self.card_width, self.card_height])
    return cube

  def make_contrast_card(self):
    """
    Build the two-colour card as two printable parts.

    The base plate carries the text in relief; the counter-plate is pierced with
    the letter shapes and fills in around them. Printed in two filament colours
    and assembled, the top surface is flush and the text finally contrasts.

    The base plate alone is also the single-piece variant: print it and swap
    filament at z = base_height to get the relief in a second colour without any
    assembly. filament_change_height() reports that height.

    Returns:
        dict[str, object]: {'single': ..., 'base': ..., 'counter': ...}
        'single' is the one-piece filament-change card, with intact letterforms.
        'base' + 'counter' are the two-piece assembly, whose letters carry the
        stencil notches that tie the counters to the counter-plate.
    """
    text_2d = self._text_2d()
    bridges_2d = self._bridges_2d()

    # Les ponts appartiennent à la contre-plaque : il faut donc les retirer des
    # lettres en relief, avec le même jeu que partout ailleurs. Le résultat est
    # une encoche fine dans la lettre — l'aspect « pochoir », obtenu ici parce
    # que c'est la seule façon de rattacher les contreformes.
    letters_2d = text_2d
    if bridges_2d is not None:
      letters_2d = text_2d - solid2.offset(delta=self.clearance)(bridges_2d)

    # Le texte est extrudé sur toute la hauteur puis uni à la plaque : le
    # recouvrement est interne, ce qui évite une coïncidence de faces à z =
    # base_height, que les mailleurs traitent mal.
    plate = solid2.linear_extrude(height=self.base_height)(self._plate_2d())
    base = plate + solid2.linear_extrude(
        height=self.base_height + self.relief_height, convexity=4)(letters_2d)

    # La variante monobloc n'a pas de contre-plaque, donc pas d'îlots et aucun
    # besoin de ponts : ses lettres gardent leur dessin intact. C'est le seul
    # avantage de lisibilité qu'elle a sur la version assemblée.
    single = plate + solid2.linear_extrude(
        height=self.base_height + self.relief_height, convexity=4)(text_2d)

    # offset() est une opération 2D : le jeu doit donc être appliqué avant
    # extrusion, d'où des booléens 2D plutôt que 3D.
    pierced = self._plate_2d() - solid2.offset(delta=self.clearance)(text_2d)
    if bridges_2d is not None:
      pierced += bridges_2d
    counter = solid2.linear_extrude(height=self.relief_height, convexity=4)(pierced)

    return {'single': single, 'base': base, 'counter': counter}

  def filament_change_height(self):
    """
    The Z height at which to swap filament for the single-piece variant.
    """
    return self.base_height

  # -- sortie -------------------------------------------------------------

  def _font_fingerprint(self):
    """
    SHA-256 of the font file, so a card can be traced back to the exact outlines
    that produced it.
    """
    digest = hashlib.sha256()
    with open(self.font_path, 'rb') as f:
      for chunk in iter(lambda: f.read(65536), b''):
        digest.update(chunk)
    return digest.hexdigest()

  def audit_header(self, extra_lines=()):
    """
    Build the comment block placed at the top of the .scad file.

    Baking outlines turns every word into hundreds of coordinates, so the words
    would otherwise be unreadable in the generated file. This restores exactly the
    auditability that text() used to provide, and exposes nothing new: the words
    are what the file is for.
    """
    lines = [
        f"Carte BIP39 — {self.key_word.getWordCount()} mots — « {_sanitize(self.title)} »",
        f"Police : {os.path.basename(self.font_path)} (sha256 {self._font_fingerprint()[:16]}…)",
        f"Taille de police : {self.base_font_size:.3f} mm",
        "Contours bakés : ce fichier ne dépend d'aucune police installée.",
    ]
    lines.extend(extra_lines)
    lines.append("")
    lines.append("Vérifiez cette table mot à mot : les mots sont devenus des")
    lines.append("polygones et c'est la seule trace lisible qu'il en reste.")
    lines.append("")
    for index, label, x, y in self.layout():
      lines.append(f"{_sanitize(label):<14} x={x:7.3f}  y={y:7.3f}")
    return "\n".join(f"// {line}".rstrip() for line in lines) + "\n"

  def save(self, filename):
    """
    Save the card to a specified file.

    :param filename: The name of the file to save the card to.
    """
    if self.data is None:
      raise RuntimeError("make_card() doit être appelé avant save().")

    print(f"Save card to {filename}")
    solid2.scad_render_to_file(self.data, filename,
                               file_header=self.audit_header())

  def save_parts(self, parts, base_path):
    """
    Save a multi-part card, one .scad per part.

    Parameters:
        parts (dict): part name -> geometry, as returned by make_contrast_card().
        base_path (str): e.g. 'card.scad' yields 'card.base.scad' and
            'card.counter.scad'.

    Returns:
        list[str]: the paths written.
    """
    root, ext = os.path.splitext(base_path)
    ext = ext or '.scad'

    written = []
    for name, geometry in parts.items():
      path = f"{root}.{name}{ext}"
      header = self.audit_header(extra_lines=[
          f"Pièce « {name} » — à imprimer séparément, dans sa propre couleur.",
          f"Variante monobloc : imprimer la pièce « base » seule et changer de "
          f"filament à z = {self.filament_change_height():.2f} mm.",
      ])
      print(f"Save card to {path}")
      solid2.scad_render_to_file(geometry, path, file_header=header)
      written.append(path)
    return written
