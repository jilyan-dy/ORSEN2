class Relation():
    id = ""
    relation = ""
    first = ""
    keywords = ""
    second = ""

    def __init__(self, id, rel, first, keywords, second):
        self.id         = id
        self.relation   = rel
        self.first      = first
        self.keywords   = keywords
        self.second     = second

    def __str__(self):
        return self.relation + " ( " + self.first +", " + self.second + " )  " + self.keywords