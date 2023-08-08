import os

class WordManager:
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Le fichier {filename} n'existe pas.")

        with open(filename, 'r') as f:
            self.words = f.read().splitlines()

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
        Get the index of a word in the list of words.

        Parameters:
            - word (str): The word to search for in the list of words.

        Returns:
            - int or None: The index of the word in the list of words, or None if the word does not exist in the list.
        """
        if self.exist(word):
            return self.words.index(word) + 1
        else:
            return None

    def getByIndex(self, index):
        """
        Retrieve a word from the list by its index.

        Parameters:
            index (int): The index of the word to retrieve.

        Returns:
            str or None: The word at the specified index, or None if the index is out of range.
        """
        if index > 0 and index <= len(self.words):
            return self.words[index - 1]
        else:
            return None

    def getBinaryIndex(self, word):
        """
        Get the binary index of a word.

        Args:
            word (str): The word to get the binary index for.

        Returns:
            str or None: The binary index of the word, or None if the index is not found.
        """
        index = self.getIndex(word)
        if index is not None:
            return bin(index)
        else:
            return None

    def getWordCount(self):
        """
        Returns the number of words in the `self.words` list.

        :return: An integer representing the count of words.
        """
        return len(self.words)