class Follow_Up:

    def __init__(self, id, template_id , follow_up_template, concept_letter):
        self.id = id
        self.template_id = template_id 
        self.follow_up_template = follow_up_template
        self.concept_letter = concept_letter
    
        self.blank_dictionary = {}
        self.blank_template = []

        self.final_response = ""
    
    def print(self):
        print("id: ", self.id)
        print("template_id: ", self.template_id)
        print("follow_up_template: ", self.follow_up_template)
        print("concept letter: ", self.concept_letter)
    
    def split_template(self):
        for word in self.follow_up_template:
            temp = word.split("_")
            self.blank_template.append(temp)
    
    def fill_blank_template(self):
        blanks = list(self.blank_dictionary.keys())

        for i in range(len(self.blank_template)):
            for j in range (len(self.blank_template[i])):
                if self.blank_template[i][j] in blanks:
                    self.blank_template[i][j] = self.blank_dictionary[self.blank_template[i][j]]
    
    def get_string_template(self):
        for i in range(len(self.blank_template)):
            for j in range (len(self.blank_template[i])):
                self.final_response += self.blank_template[i][j]
            
            if i != len(self.blank_template)-1:
                self.final_response += " ||| "
        
        return self.final_response 
    
    '''
    def get_string_template(self):
    for i in range(len(self.blank_template)):
        temp = ""
        for j in range (len(self.blank_template[i])):
            emp += self.blank_template[i][j]
        print(temp)
    '''
                

