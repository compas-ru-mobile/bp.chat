
WORD_TYPE_SIMPLE = 0
WORD_TYPE_LINK = 1


class Word(str):

    @staticmethod
    def __new__(cls, word: str, word_type: int = WORD_TYPE_SIMPLE):
        obj = str.__new__(cls, word)
        obj.word_type = word_type
        return obj


class LinkWord(Word):

    @staticmethod
    def __new__(cls, word: str, url: str):
        obj = Word.__new__(cls, word=word, word_type=WORD_TYPE_LINK)
        obj.url = url
        return obj


class LineContinue(str):

    @staticmethod
    def __new__(cls, word: str, word_type: int = WORD_TYPE_SIMPLE):
        obj = str.__new__(cls, word)
        obj.word_type = word_type
        return obj

