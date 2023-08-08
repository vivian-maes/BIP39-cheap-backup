import argparse

from libs.word_manager import WordManager
from libs.card_dessing import CardDessing

def main(key_path, tile, save_path):
    print(f"Fichier à lire = {key_path}")

    key_word = WordManager(key_path)

    if key_word.getWordCount() != 24 and key_word.getWordCount() != 18 and key_word.getWordCount() != 12:
        raise Exception(f"Le fichier {key_path} ne contient pas 24, 18 ou mots")

    card_dessing = CardDessing(key_word, tile)
    card_dessing.make_card()
    card_dessing.save(save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mon application Python en ligne de commande.')
    
    parser.add_argument('key_path',  type=str, help='path vers le fichier à encoder.')
    parser.add_argument('title',     type=str, help='titre de la carte.')
    parser.add_argument('save_path', type=str, help='path du fichier à savegarder.')

    args = parser.parse_args()

    main(args.key_path, args.title, args.save_path)
