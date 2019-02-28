class Move:

    def __init__(self, move_id=-1, response_type="", template=[], blanks=[], blank_index=[], type_num=-1, subject=None):
        self.move_id = move_id
        self.type = type
        self.template = template
        self.blanks = blanks
        self.response_type = response_type
        self.blank_index = blank_index
        self.type_num = type_num
        self.subject = subject

    def fill_blank(self, fill):
        for i in range(0, len(fill)):
            self.template[self.blank_index[i]] = fill[i]

    def get_string_response(self):
        string = ""

        for s in self.template:
            string += str(s)

        return string

    def __str__(self):
        string = "MOVE:" + self.response_type +"\n"+ str(self.template) +\
                "\n" + str(self.blanks) + "\n" + str(self.blank_index)+"\n"
        if self.subject is not None:
            string += str(self.subject.name)+" : "+repr(self.subject)
        else:
            string += "No subject."

        return string