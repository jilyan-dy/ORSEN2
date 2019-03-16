from numpy import random
from src.objects.ServerInstance import ServerInstance
from src.inputprocessor.infoextraction import getCategory, CAT_STORY, CAT_COMMAND, CAT_ANSWER
from src.dialoguemanager import DBO_Move, Move
from src.db.concepts import DBO_Concept, DBO_Local_Concept
from src.objects.concepts.Concept import Concept
from src.objects.eventchain.EventFrame import EventFrame, FRAME_EVENT, FRAME_DESCRIPTIVE
from src.dialoguemanager.story_generation import to_sentence_string, get_subject_string

from src.objects.storyworld.Character import Character
from src.objects.storyworld.Object import Object

import random as ran

STORY_THRESHOLD = 3
GENERAL_RESPONSE_THRESHOLD = 5

#what score should be met to change the dbtype "local" to "global"
SCORE_THRESHOLD = 5

MOVE_FEEDBACK = 1
MOVE_GENERAL_PUMP = 2
MOVE_SPECIFIC_PUMP = 3
MOVE_HINT = 4
MOVE_REQUESTION = 5
MOVE_UNKNOWN = 6
MOVE_PROMPT = 7
MOVE_SUGGESTING = 8

NODE_START = 0
NODE_END = 1
NODE_EITHER = 2

CONVERT_INFINITIVE = "inf"
CONVERT_1PRSG = "1sg"
CONVERT_2PRSG = "2sg"
CONVERT_3PRSG = "3sg"
CONVERT_PRPL = "pl"
CONVERT_PRPART = "part"

CONVERT_PAST = "p"
CONVERT_1PASG = "1sgp"
CONVERT_2PASG = "2sgp"
CONVERT_3PASG = "3sgp"
CONVERT_PAPL = "ppl"
CONVERT_PAPART = "ppart"

#DATABASE_TYPE

server = ServerInstance()

def retrieve_output(coreferenced_text, world_id):
    world = server.get_world(world_id)
    if len(world.responses) > 0:
        last_response_type_num = world.responses[len(world.responses)-1].type_num
    else:
        last_response_type_num = -1
    output = ""
    choice = -1

    if len(world.event_chain) <=  1 and ("my name is" in coreferenced_text or
            (("hello" in coreferenced_text or "hi" in coreferenced_text)
                  and ("I am" in coreferenced_text or "I'm" in coreferenced_text)) ):
        return Move.Move(template=["Nice to meet you! So how does your story start?"], type_num=MOVE_REQUESTION)

    if coreferenced_text == "":  # if no input found
        world.empty_response += 1

        if world.empty_response == 1:
            if last_response_type_num in [MOVE_FEEDBACK, MOVE_HINT]:
                output = Move.Move(template=["I'm sorry, I did not understand what you just said. Can you say it again?"], type_num=MOVE_REQUESTION)
            elif last_response_type_num == MOVE_GENERAL_PUMP:
                output = generate_response(MOVE_SPECIFIC_PUMP, world, [], coreferenced_text)
            elif last_response_type_num == MOVE_SPECIFIC_PUMP:
                output = generate_response(MOVE_HINT, world, [], coreferenced_text)
                output.template = ["What if "]+output.template
            else:
                output = Move.Move(template=["I'm not sure I heard you?"], type_num=MOVE_REQUESTION)

        if world.empty_response >= 2 and world.empty_response <=4:
            if last_response_type_num == MOVE_GENERAL_PUMP:
                output = generate_response(MOVE_SPECIFIC_PUMP, world, [], coreferenced_text)
            elif last_response_type_num == MOVE_SPECIFIC_PUMP:
                output = generate_response(MOVE_HINT, world, [], coreferenced_text)
                output.template = ["What if "] + output.template
            else:
                choice = random.randint(MOVE_GENERAL_PUMP, MOVE_SPECIFIC_PUMP+1)
                output = generate_response(choice, world, [], coreferenced_text)

        elif world.empty_response > 4:
            choice = MOVE_REQUESTION
            output = Move.Move(template=["I don't think I can hear you, are you sure you want to continue?"], type_num=choice)
    else:
        world.empty_response = 0
        category = getCategory(coreferenced_text)

        if category == CAT_STORY:
            print(len(world.event_chain))
            if len(world.event_chain) <= STORY_THRESHOLD:
                print("<< STILL IN GENERALIZED THRESHOLD >>")
                choice = random.randint(MOVE_FEEDBACK, MOVE_GENERAL_PUMP+1)
            elif world.general_response_count == GENERAL_RESPONSE_THRESHOLD:
                print("<< GENERAL THRESHOLD REACHED - ATTEMPTING SPECIFIC RESPONSE >>")
                choice = random.randint(MOVE_SPECIFIC_PUMP, MOVE_SPECIFIC_PUMP+1)
            else:
                #choice = random.randint(MOVE_FEEDBACK, MOVE_SPECIFIC_PUMP+1)
                choice = world.compute_weights_dialogue()

            output = generate_response(choice, world, [], coreferenced_text)

        elif category == CAT_ANSWER:
            # TEMP TODO: idk how to answer this lmao / if "yes" or whatever, add to character data
            if last_response_type_num == MOVE_REQUESTION:
                output = Move.Move(template=["Ok, let's keep going then!"], type_num=MOVE_UNKNOWN)
            
            if last_response_type_num == MOVE_SUGGESTING:
                if "yes" in coreferenced_text:
                    world.continue_suggesting = 0
                    world.suggest_continue_count = 0

                    last_response_concept_id = world.responses[len(world.responses)-1].concept_id

                    #Get the entire local concept
                    local_concept = DBO_Local_Concept.get_concept_by_id(last_response_concept_id)
                    new_score = local_concept.score + 1.0     #Add the score
                    DBO_Local_Concept.update_score(last_response_concept_id, new_score) #Update the score

                    #If score exceeds, change assertion/concept type to global
                    if new_score >= SCORE_THRESHOLD:
                        DBO_Local_Concept.update_valid(last_response_concept_id, 0)
                        #DBO_Concept.add_concept(Concept(local_concept.id, local_concept.first, local_concept.relation, local_concept.second))

                    #NEW RESPONSE
                    output = Move.Move(template=["Ok, let's keep going then!"], type_num=MOVE_UNKNOWN)
                
                elif "no" in coreferenced_text:
                    output = Move.Move(template=["Why not? Don't you like it or do you think it's wrong?"], type_num=MOVE_UNKNOWN)
                    world.continue_suggesting = 1
                
                else:
                    output = Move.Move(template=["Sorry, I don't understand. Please answer by yes or no"], type_num=MOVE_SUGGESTING)

            elif last_response_type_num == MOVE_UNKNOWN and world.continue_suggesting == 1:  
                if "don't like" in sentence or "dont like" in sentence:
                    choice = MOVE_SUGGESTING
                    output = generate_response(choice, world, [], coreferenced_text)

                elif "wrong" in sentence:
                    print("NOT YET DONE")
                
                if world.suggest_continue_count == 3:
                    choice = MOVE_SPECIFIC_PUMP
                    output = generate_response(choice, world, [], coreferenced_text)

            else:
                choice = random.randint(MOVE_FEEDBACK, MOVE_HINT+1)
                output = generate_response(choice, world, [], coreferenced_text)

        elif category == CAT_COMMAND:
            # TEMP TODO: check for further commands
            choice = random.randint(MOVE_FEEDBACK, MOVE_SPECIFIC_PUMP+1)

            is_hint = "your turn" in coreferenced_text or \
                        ("suggest" in coreferenced_text and "sentence" in coreferenced_text) or \
                        ("give" in coreferenced_text and "hint" in coreferenced_text)

            is_pump = ("what" in coreferenced_text and \
                       ("say" in coreferenced_text or "next" in coreferenced_text or "talk" in coreferenced_text))

            is_either = "help" in coreferenced_text or \
                            "stuck" in coreferenced_text or \
                            ("give" in coreferenced_text and "idea" in coreferenced_text)
            
            is_suggesting = "trial" in coreferenced_text

            if "help me start" in coreferenced_text:
                output = generate_response(MOVE_PROMPT, world, [], coreferenced_text)
                world.add_response(output)
                return output

            # if len(world.responses) == 0:
            #     concepts = DBO_Concept.get_concept_like(txt_relation, second=txt_concept)
            if is_either:
                choice = random.randint(MOVE_GENERAL_PUMP, MOVE_HINT+1)
            elif is_hint:
                choice = MOVE_HINT
            elif is_pump:
                choice = random.randint(MOVE_GENERAL_PUMP, MOVE_SPECIFIC_PUMP+1)
            
            elif is_suggesting:
                choice = MOVE_SUGGESTING

            output = generate_response(choice, world, [], coreferenced_text)

        else:
            output = Move.Move(template=["I don't know what to say."], type_num=MOVE_UNKNOWN)
    
    if output.type_num == MOVE_SUGGESTING:
        world.continue_suggesting = 1
    elif output.type_num != MOVE_UNKNOWN:
        world.continue_suggesting = 0

    world.add_response(output)
    world.add_response_type_count(output)

    return output

#Note this one is when a move_code has been decided. If there is no concepts then change move_code to feedback.
def generate_response(move_code, world, remove_index, text):

    #DBO should be accessing the local concept
    DATABASE_TYPE = DBO_Concept
    if move_code == MOVE_SUGGESTING:
        DATABASE_TYPE = DBO_Local_Concept
    else:
        DATABASE_TYPE = DBO_Concept

    print(DATABASE_TYPE)

    choices = []
    subject = None

    if len(world.responses) > 0:
        last_response_id = world.responses[len(world.responses)-1].move_id
    else:
        last_response_id = -1

    if move_code == MOVE_FEEDBACK:

        pre_choices = DBO_Move.get_templates_of_type(DBO_Move.TYPE_FEEDBACK)

        if len(world.event_chain) > 0:
            last = world.event_chain[len(world.event_chain)-1]
            for item in pre_choices:
                if last.event_type == FRAME_EVENT and "happen" in item.get_string_response():
                    choices.append(item)
                if "happen" not in item.get_string_response():
                    choices.append(item)
        else:
            choices = pre_choices

    elif move_code == MOVE_GENERAL_PUMP:
        pre_choices = DBO_Move.get_templates_of_type(DBO_Move.TYPE_GENERAL_PUMP)

        if len(world.event_chain) > 0:
            last = world.event_chain[len(world.event_chain)-1]
            for item in pre_choices:
                if last.event_type == FRAME_EVENT and "happen" in item.get_string_response():
                    choices.append(item)
                if "happen" not in item.get_string_response():
                    choices.append(item)
        else:
            choices = pre_choices

    elif move_code == MOVE_SPECIFIC_PUMP:
        choices = DBO_Move.get_templates_of_type(DBO_Move.TYPE_SPECIFIC_PUMP)

    elif move_code == MOVE_HINT:
        choices = DBO_Move.get_templates_of_type(DBO_Move.TYPE_HINT)
    
    elif move_code == MOVE_SUGGESTING:
        choices = DBO_Move.get_templates_of_type(DBO_Move.TYPE_SUGGESTING)

    elif move_code == MOVE_REQUESTION:
        # TODO: requestioning decisions to be made
        choices = ["requestioning..."]
    elif move_code == MOVE_PROMPT:
        choices = DBO_Move.get_templates_of_type("prompt")
        usable_concepts = DATABASE_TYPE.get_concept_like("IsA", second="role")
        choice = random.randint(0, len(choices))
        choice2 = random.randint(0, len(usable_concepts))
        if len(usable_concepts) > 0:
            move = choices[choice]
            a = []
            a.append(usable_concepts[choice2].first)
            move.fill_blank(a)

            print("FINAL MOVE DECISION:")
            print(str(move))
            move.subject = subject
            return move

    index_loop = 0

    #This is where move was first initialize
    while True:
        index_loop += 1
        index = random.randint(0, len(choices))
        move = choices[index]

        # Check if the template has already been use through move.move_id
        # Dapat hindi siya yun last na use. Dapat hindi siya nasa remove_index
        if move.move_id != last_response_id and move.move_id not in remove_index:
            print("NANDITO AKO")
            move.type_num = move_code
            break

        print(index_loop)
        if index_loop > 20:
            print("AM I HERE?????")
            remove_index.append(move.move_id)
            return generate_response(MOVE_FEEDBACK, world, remove_index, text)

    print("Generating fillable template...")
    print(str(move))

    for blank_type in move.blanks:

        has_a_specified_concept = ":" in blank_type

        if has_a_specified_concept:
            split_relation = str(blank_type).split(":")
            relation_index = -1
            replacement_index = -1

            for i in range(0, len(split_relation)):
                if split_relation[i] in DATABASE_TYPE.RELATIONS:
                    relation_index = i
                else:
                    replacement_index = i

            usable_concepts = []
            txt_relation = split_relation[relation_index]
            to_replace = split_relation[replacement_index]

            if to_replace in ["setting"]:
                if to_replace == "setting":
                    print("SETTING DECISION:")
                    if subject is None or subject.inSetting['LOC'] is None:
                        remove_index.append(move.move_id)
                        print("No viable SUBJECT or SUBJECT LOCATION... switching move.")
                        return generate_response(move_code, world, remove_index, text)
                    else:
                        txt_concept = subject.inSetting['LOC']

            else:
                txt_concept = to_replace

            if relation_index == 0:
                usable_concepts = DATABASE_TYPE.get_concept_like(txt_relation, second=txt_concept)
            elif relation_index == 1:
                usable_concepts = DATABASE_TYPE.get_concept_like(txt_relation, first=txt_concept)
            else:
                print("ERROR: Index not found.")
            
            #if may laman ang usable_concepts
            if len(usable_concepts) > 0 :
                concept_string = ""
                concept_index = random.randint(0,len(usable_concepts)) #randomize it, get one

                if relation_index == 0:
                    concept_string = usable_concepts[concept_index].first #get the first concept
                elif relation_index == 1:
                    concept_string = usable_concepts[concept_index].second

                move.template[move.template.index(to_replace)] = concept_string #from the templates, look for the index of the to_replace

        elif blank_type in DATABASE_TYPE.RELATIONS:

            # CHOOSE THE CONCEPT
            decided_concept = ""
            decided_node = -1

            loop_total = 0

            if subject is None:

                charas = world.get_top_characters()
                objects = world.get_top_objects()
                list_choices = charas + objects

                while True:
                    if len(list_choices) > 0:
                        loop_total += 1
                        choice_index = random.randint(0, len(list_choices))
                        decided_item = list_choices[choice_index]
                    else:
                        print("AAAAaAA")
                        break

                    subject = decided_item
                    print("CELINA - SUBJECT: - " + str(subject))
                    print(type(subject))
                    print(subject.type)

                    if len(subject.type) > 0:
                        print("HOPIA")
                        decided_concept = subject.name[random.randint(0, len(subject.type))]
                        decided_node = NODE_START
                    else:
                        if isinstance(decided_item, Object):
                            decided_concept = decided_item.name
                            subject = decided_item
                            decided_node = NODE_START
                            print(decided_concept)
                            print("OBJECT KA BA")

                        #NEVER ATA DUMAAN DITO SA ELIF, di ko alam para saan ito
                        elif isinstance(decided_item, Character):
                            # get... something... relationship??
                            # TODO: use relationship or something to get a concept
                            found_attr = DATABASE_TYPE.HAS_PROPERTY
                            decided_concept = decided_item.name
                            subject = decided_item

                            if blank_type == DATABASE_TYPE.HAS_PREREQ or blank_type == DATABASE_TYPE.CAUSES:
                                found_attr = DATABASE_TYPE.CAPABLE_OF
                                decided_node = NODE_START

                            elif blank_type == DATABASE_TYPE.IS_A or blank_type == DATABASE_TYPE.PART_OF or DATABASE_TYPE.USED_FOR:
                                found_attr = DATABASE_TYPE.IS_A
                                decided_node = NODE_START
                            
                            elif blank_type == DATABASE_TYPE.CAPABLE_OF:
                                print("HI LANG")
                                
                            for item in decided_item.attributes:
                                if item.relation == found_attr and not item.isNegated:
                                    decided_concept = item.name
                                    break

                            if decided_concept == "":
                                remove_index.append(move.move_id)
                                return generate_response(move_code, world, remove_index, text)

                    if decided_node != -1 or loop_total > 10:
                        break

                if blank_type == DATABASE_TYPE.AT_LOCATION:

                    settings = world.settings

                    print(len(settings))
                    if len(settings) > 0:
                        decided_concept = settings[ran.choice(list(settings.keys()))].name
                        decided_node = NODE_END
                    else:
                        remove_index.append(move.move_id)
                        return generate_response(move_code, world, remove_index, text)
            # find
            # This part looks for the concept. Example Girl went to mall. So if decided_node is NODE_END. 
            # It would look for concepts na ang second ay mall
            if decided_node == NODE_START:
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type, first=decided_concept)
            elif decided_node == NODE_END:
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type, second=decided_concept)
            elif decided_node == NODE_EITHER: #Not being used
                usable_concepts = DATABASE_TYPE.get_concept(decided_concept, blank_type)
            else:
                usable_concepts = []
                
            #TO DO, check if suggesting yung move then you have to check whether local ot global yun concept
            #TO DO, check the user rin

            #If there is none found, change template.
            if len(usable_concepts) == 0:
                remove_index.append(move.move_id)
                print("Hi friends")
                print(loop_total)
                return generate_response(move_code, world, remove_index, text)

            while len(usable_concepts) == 0:
                loop_total += 1
                print("Hi friends 2")
                print(loop_total)
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type)
                if loop_total > 10:
                    print("Hi friends 3")
                    break
                    
            print("DECIDED CONCEPT: "+decided_concept)
            print(str(usable_concepts))
            if len(usable_concepts) > 0:
                concept_index = random.randint(0,len(usable_concepts))
                concept = usable_concepts[concept_index]
                move.template[move.template.index("start")] = concept.first
                move.template[move.template.index("end")] = concept.second
                
                # Get the concept id, this is for adding the score
                move.concept_id = concept.id
                print("CELINNA HHHIII") #REMOVE PRINT
                print(move.concept_id)
            else:
                print("ERROR: NO USABLE CONCEPTS decided:",decided_concept)
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)

        elif blank_type == "Object":

            if subject is None:
                charas = world.get_top_characters()
                objects = world.get_top_objects()
                list_choices = charas + objects

                choice_index = random.randint(0, len(list_choices))
                subject = list_choices[choice_index]

            move.template[move.template.index("object")] = subject.id

        elif blank_type == "Item":

            if subject is None:
                objects = world.get_top_objects()

                if len(objects) > 0:
                    choice_index = random.randint(0, len(objects))
                    subject = objects[choice_index]
                else:
                    remove_index.append(move.move_id)
                    return generate_response(move_code, world, remove_index, text)

            move.template[move.template.index("item")] = subject.id

        elif blank_type == "Character":
            if subject is None or not isinstance(subject, Character):
                charas = world.get_top_characters(5)

                if len(charas) > 0:
                    choice_index = random.randint(0, len(charas))
                    subject = charas[choice_index]
                else:
                    remove_index.append(move.move_id)
                    return generate_response(move_code, world, remove_index, text)
            else:
                chara = subject

            move.template[move.template.index("character")] = subject.id

        elif blank_type == "inSetting":
            if subject is None:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)
            elif subject.inSetting is None:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)
            else:
                move.template[move.template.index("inSetting")] = subject.inSetting['LOC']

        elif blank_type == "Repeat":

            if len(world.event_chain) > 0:
                move.template[move.template.index("repeat")]\
                    = to_sentence_string(world.event_chain[len(world.event_chain)-1])
            else:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)

        elif blank_type == "Pronoun":
            if subject is None:
                move.template[move.template.index("pronoun")] = "it"
            else:
                if isinstance(subject, Object):
                    move.template[move.template.index("pronoun")] = "they"
                elif subject.gender == "":
                    move.template[move.template.index("pronoun")] = "they"
                elif subject.gender == "M":
                    move.template[move.template.index("pronoun")] = "he"
                elif subject.gender == "F":
                    move.template[move.template.index("pronoun")] = "she"
                else:
                    move.template[move.template.index("pronoun")] = subject.name

        elif blank_type == "Event":
            loop_back = len(world.event_chain)-1
            loops = 0
            while loop_back >= 0 and loops < 5:
                event = world.event_chain[loop_back]

                if event.event_type == FRAME_EVENT:
                    if event.action != "":
                        if "eventverb" in move.template:
                            move.template[move.template.index("eventverb")] = event.action
                        if "object" in move.template:
                            move.template[move.template.index("object")] = get_subject_string(event)

                loop_back -= 1
                loops += 1

            if loop_back == -1 or loops >= 5:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)
        
    if move_code == MOVE_SUGGESTING:
        move.template.insert(0, "What if ")
        move.template.append("?")

    print("FINAL MOVE DECISION:")
    print(str(move))
    move.subject = subject
    return move

