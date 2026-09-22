import argparse

from libs.word_manager import WordManager
from libs.card_dessing import CardDessing

# Longueurs de mnémonique définies par BIP39. Les variantes 15 et 21 étaient
# refusées alors que la mise en page les gère (5 et 7 rangées de 3 mots).
VALID_WORD_COUNTS = (12, 15, 18, 21, 24)

def main(key_path, tile, save_path):
    print(f"Fichier à lire = {key_path}")

    key_word = WordManager(key_path)

    word_count = key_word.getWordCount()
    if word_count not in VALID_WORD_COUNTS:
        expected = ", ".join(str(n) for n in VALID_WORD_COUNTS)
        raise Exception(
            f"Le fichier {key_path} contient {word_count} mots ; "
            f"une clé BIP39 en compte {expected}.")

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
