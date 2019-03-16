import spacy
from src.objects.ServerInstance import ServerInstance
from src.objects.storyworld.World import World
from src.inputprocessor import infoextraction
from src.dialoguemanager import DialoguePlanner
from src.dialoguemanager.story_generation import generate_basic_story, generate_collated_story

server = ServerInstance()
#Loading of text and segmentation of sentences
nlp = spacy.load('en_coref_sm')
doc = nlp(u'My sister has a dog. She loves him.')
print(doc._.coref_clusters)

def new_world(id):
    global world_id
    world_id = id
    server.new_world(world_id)

def extract_info(text):
    print("EXTRACTING........")
    list_of_sentences = []
    characters = []

    world = server.get_world(world_id)
    document = nlp(str(text[len(text)-1]))
    sentences_curr = [sent.string.strip() for sent in document.sents]
    sentences_curr = sentences_curr[0]
    # Part-Of-Speech, NER, Dependency Parsing
    sentences_curr = nlp(sentences_curr) # go thru spacy
    print(sentences_curr)
    list_of_sentences.append(infoextraction.pos_ner_nc_processing(sentences_curr))
    
    if len(text) > 1:
        document = nlp(str(text[len(text)-2]))
        sentences_prev = [sent.string.strip() for sent in document.sents]
        sentences_prev = sentences_prev[0]
        sentences_prev = nlp(sentences_prev) # go thru spacy
        list_of_sentences.append(infoextraction.pos_ner_nc_processing(sentences_prev))

    # DetailsExtraction
    if len(text) > 1:
        list_of_sentences[0] = infoextraction.coref_resolution(list_of_sentences[0], list_of_sentences[0], list_of_sentences[1], world, False)

    # for s in sentences:
    #     s = nlp(s)
    #     list_of_sent.append(infoextraction.pos_ner_nc_processing(s))

    infoextraction.details_extraction(list_of_sentences[0], world, "ROOT")
    infoextraction.event_extraction(list_of_sentences[0], world, "ROOT")

    print("-------- CHARACTERS")
    for c in world.characters:
        print(world.characters[c])
        for a in world.characters[c].attributes:
            print("attr", a.relation, a.name, a.isNegated)

    print("-------- OBJECTS")
    for c in world.objects:
        print(world.objects[c])
        for a in world.objects[c].attributes:
            print("attr", a.relation, a.name, a.isNegated)

    print("-------- SETTINGS")
    for s in world.settings:
        print(world.settings[s])

    print("-------- EVENT CHAIN")
    for e in world.event_chain:
        print(str(e))

    # For Event Extraction
    seq_no = []
    event_type = []
    doer = []
    doer_act = []
    rec = []
    rec_act = []
    location = []
    event_frame = [seq_no, event_type, doer, doer_act, rec, rec_act, location]

    extracted = None
    
    # extract all possible relations from sentence input
    extracted = infoextraction.extract_relation(list_of_sentences[0])

    # remove relations that already exist in the global kb
    extracted = infoextraction.remove_existing_relations_global(extracted)

    # remove relations that already exist in the local kb
    extracted = infoextraction.remove_existing_relations_local(-1, extracted)

    # add new relations to local kb
    if extracted != []:
        infoextraction.add_relations_to_local(-1, extracted) # Jilyan How will you get the user id???
    else:
        result = infoextraction.find_unkown_word(list_of_sentences[0]) # pass this to celina


'''
output = "Hello, I am ORSEN. Let's start."
retrieved = None
world_id = "0"
new_world(world_id)
while True:
    if retrieved is not None:
        output = retrieved.get_string_response()
        print("IN: "+text)
    text = input("OUT: " + output + "\n")

    if infoextraction.getCategory(text) == infoextraction.CAT_STORY:
        extract_info(text)

    #dialogue
    retrieved = DialoguePlanner.retrieve_output(text, world_id)

    if retrieved.type_num == DialoguePlanner.MOVE_HINT:
        extract_info(retrieved.get_string_response())

    if text == "The end":
        print("FINAL STORY -----------------")
        print(generate_collated_story(server.get_world(world_id)))
        print("-----------------------------")
'''