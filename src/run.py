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
    world = server.get_world(world_id)
    document = nlp(str(text))
    sentences = [sent.string.strip() for sent in document.sents]
    list_of_sentences = []
    list_of_sent = []
    characters = []

    # Part-Of-Speech, NER, Dependency Parsing
    for sent in sentences:
        sent = nlp(sent) # go thru spacy
        list_of_sentences.append(infoextraction.pos_ner_nc_processing(sent))

    list = []
    curr = 0
    bef = 0
    isFirst = False

    # DetailsExtraction
    for sent in list_of_sentences:
        if curr == 1 or curr > 1:
            sentences[curr] = infoextraction.coref_resolution(sent, sentences[curr], sentences[bef], world, False)
        else:
            sentences[curr] = infoextraction.coref_resolution(sent, sentences[curr], sentences[curr], world, True)

        curr += 1
        if bef == 0 and curr == 1:
            print("oops")
        else:
            bef += 1

    for s in sentences:
        s = nlp(s)
        list_of_sent.append(infoextraction.pos_ner_nc_processing(s))

    for s in list_of_sent:
        infoextraction.details_extraction(s, world, "ROOT")
        infoextraction.event_extraction(s, world, "ROOT")

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