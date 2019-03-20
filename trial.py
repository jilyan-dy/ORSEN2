from src.dialoguemanager import Follow_Up, DBO_Follow_Up

print("hello")

k = DBO_Follow_Up.get_specific_follow_up_template(2)
# k.print() #Check if na lilipat

#DICTIONARY
dict = {}
dict["character"] = "Irene"
dict["start"] = "mic"
dict["end"] = "sing"

k.blank_dictionary = dict
##DICTIONARY

k.split_template()

k.fill_blank_template()

k.get_string_template()