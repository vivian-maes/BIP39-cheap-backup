class WordManager:
    def __init__(self, filename):
        # Pas de pré-vérification d'existence : elle ouvrirait une fenêtre TOCTOU
        # et open() lève déjà FileNotFoundError.
        try:
            # encoding explicite : sans lui, une wordlist non anglaise se décode
            # selon la locale de la machine et finit en mojibake gravé sur la carte.
            with open(filename, 'r', encoding='utf-8') as f:
                # strip + filtrage : une ligne vide finale, très courante dans un
                # fichier édité à la main, compterait sinon comme un mot.
                self.words = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Le fichier {filename} n'existe pas.")

    def exist(self, word):
        """
        Check if a word exists in the list of words.

        Parameters:
            word (str): The word to check.

        Returns:
            bool: True if the word exists, False otherwise.
        """
        return word in self.words

    def getIndex(self, word):
        """
        Get the position of the first occurrence of a word.

        A BIP39 mnemonic may legitimately repeat a word; only the first position
        is returned. Use getIndices() to address every occurrence.

        Parameters:
            - word (str): The word to search for in the list of words.

        Returns:
            - int or None: The 1-based position of the word, or None if absent.
        """
        if self.exist(word):
            return self.words.index(word) + 1
        else:
            return None

    def getIndices(self, word):
        """
        Get every position at which a word occurs.

        Parameters:
            word (str): The word to search for.

        Returns:
            list[int]: The 1-based positions, empty if the word is absent.
        """
        return [i for i, w in enumerate(self.words, start=1) if w == word]

    def getByIndex(self, index):
        """
        Retrieve a word from the list by its index.

        Parameters:
            index (int): The 1-based index of the word to retrieve.

        Returns:
            str or None: The word at the specified index, or None if the index is
            out of range or is not an integer (getIndex returns None on a miss, so
            getByIndex(getIndex(w)) must not raise).
        """
        if not isinstance(index, int) or isinstance(index, bool):
            return None
        if index > 0 and index <= len(self.words):
            return self.words[index - 1]
        else:
            return None

    def getBinaryIndex(self, word):
        """
        Get the BIP39 binary index of a word: a zero-based, 11-bit field.

        Note that the index is a position within the file handed to this class,
        not a position in the official BIP39 wordlist, which is never consulted.

        Args:
            word (str): The word to get the binary index for.

        Returns:
            str or None: An 11-character string of '0'/'1', or None if the word is
            absent or its position exceeds the 2048-entry BIP39 range.
        """
        index = self.getIndex(word)
        if index is None:
            return None
        if index > 2048:
            return None
        return format(index - 1, '011b')

    def getWordCount(self):
        """
        Returns the number of words in the `self.words` list.

        :return: An integer representing the count of words.
        """
        return len(self.words)
