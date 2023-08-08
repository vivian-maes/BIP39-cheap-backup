import solid
from solid.utils import *

class CardDessing:
  def __init__(self, key_word, title):
    self.key_word   = key_word
    self.title      = title

    self.margin       = 2
    self.word_margin  = 1

    self.card_height  = 1.0
    self.card_width   = 55.0
    self.card_length  = 85.0

    self.font_name    = 'Futura'
    self.text_height  = ( self.card_height / 2 ) + 0.1
    self.text_z_pos   = self.card_height - (self.card_height / 2)

    self.base_font_size    = 3.5
    self.title_font_size   = self.base_font_size * 1.2

    self.word_by_line   = 3
    self.rows           = self.key_word.getWordCount() // self.word_by_line

    row_lost_space      = (self.margin * 2) + ((self.word_by_line - 1) * self.word_margin)
    self.max_size_word  = (self.card_length - row_lost_space) / self.word_by_line

    self.top_text_zone  = self.card_width - (self.margin * 2.5 ) - self.title_font_size
    self.row_height     = self.top_text_zone / self.rows



  def make_card(self):
    """
    Make a card by performing the following steps:
    1. Initialize the base card by calling the make_card_base() method.
    2. Subtract the value returned by the write_title() method, this write the title on the card.
    3. Call the lay_out_text() method to lay out the text.

    This method does not take any parameters.

    This method does not return anything.
    """
    self.data = self.make_card_base()
    self.data -= self.write_title(self.title)
    self.lay_out_text()


  def make_card_base(self):
    """
    Generates the base of a card.

    Returns:
        cube: A solid object representing the base of the card.
    """
    cube = solid.cube([self.card_length, self.card_width, self.card_height])
    return cube

  def write_title(self, tile):
    """
    Writes the title of a card.

    Args:
        tile (str): The title text to be written on the card.

    Returns:
        solid.text: The text object representing the written title.
    """
    y = self.card_width - self.margin - self.title_font_size  # + (self.font_size / 3)
    x = self.card_length / 2
    text = solid.translate([x, y, self.text_z_pos])(
        solid.linear_extrude(height=self.text_height, convexity=None)(
            solid.text(tile, size=self.title_font_size, font=self.font_name, halign='center', valign='baseline',
                       spacing=1.0)))
    return text

  def lay_out_text(self):
    """
    Lays out the text  on the card.

    Parameters:
    - word_index: The index of the current word.
    - row: The row of the current word.
    - word: The position of the current word in its row.
    - x: The x-coordinate of the current word.
    - y: The y-coordinate of the current word.
    - word_text: The text of the current word.

    Returns:
    - None

    Note:
    - This function dispose all text on the cad (data).
    """
    for word_index in range(1, self.key_word.getWordCount() + 1):
      row = (word_index -1) // self.word_by_line
      row = self.rows - row
      word = word_index - ((self.rows - row) * self.word_by_line)
    
      x = self.margin + ((word - 1) *  self.word_margin) + ((word - 1) *  self.max_size_word)
      y = ((row - 1) * self.row_height) + self.margin

      word_text = f"{str(word_index).zfill(2)} {self.key_word.getByIndex(word_index)}"

      self.data -= self.write_word(word_text, x, y)
    

  def write_word(self, word, x, y):
    """
        Writes a word on the 3D canvas at a specific location.

        Args:
            word (str): The word to write on the canvas.
            x (float): The x-coordinate of the starting position of the word.
            y (float): The y-coordinate of the starting position of the word.

        Returns:
            text: The 3D text object representing the written word.
    """
    text = solid.translate([x, y, self.text_z_pos])(
        solid.linear_extrude(height=self.text_height, convexity=None)(
            solid.text(word, size=self.base_font_size, font=self.font_name, halign='left', valign='baseline',
                       spacing=1.0)))
    return text


  def save(self, filename):
    """
    Save the card to a specified file.
    
    :param filename: The name of the file to save the card to.
    """
    print(f"Save card to {filename}")
    solid.scad_render_to_file(self.data, filename)
