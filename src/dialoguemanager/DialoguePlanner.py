from numpy import random
from src.objects.ServerInstance import ServerInstance
from src.inputprocessor.infoextraction import getCategory, CAT_STORY, CAT_COMMAND, CAT_ANSWER
from src.dialoguemanager import DBO_Move, Move
from src.dialoguemanager import Follow_Up, DBO_Follow_Up
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

server = ServerInstance()

def retrieve_output(coreferenced_text, world_id, userid):
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

        if len(world.responses) >= 3:
            if (last_response_type_num == MOVE_UNKNOWN and world.responses[len(world.responses)-3].type_num == MOVE_SUGGESTING):
                if coreferenced_text == world.responses[len(world.responses)-1].concept_letter:
                    concept_id = world.responses[len(world.responses)-1].concept_id
                    local_concept = DBO_Local_Concept.get_concept_by_id(concept_id)

                    if local_concept.userid != userid:
                        new_score = local_concept.score - 1.5     #Minus the score
                        DBO_Local_Concept.update_score(concept_id, new_score) #Update the score

                category = -1    
        
        if category == -1:
            output = suggest_again(world, coreferenced_text)

        elif category == CAT_STORY:
            # print("world", len(world.event_chain))
            #if world.general_response_count < 3:
            #    choice = MOVE_SUGGESTING

            if len(world.event_chain) <= STORY_THRESHOLD:
                print("<< STILL IN GENERALIZED THRESHOLD >>")
                choice = random.randint(MOVE_FEEDBACK, MOVE_GENERAL_PUMP+1)
                #choice = MOVE_FEEDBACK
            elif world.general_response_count == GENERAL_RESPONSE_THRESHOLD:
                print("<< GENERAL THRESHOLD REACHED - ATTEMPTING SPECIFIC RESPONSE >>")
                choice = random.randint(MOVE_SPECIFIC_PUMP, MOVE_SPECIFIC_PUMP+1)
            else:
                #choice = random.randint(MOVE_FEEDBACK, MOVE_SPECIFIC_PUMP+1)

                #WEIGHTED RANDOMIZER
                choice = world.compute_weights_dialogue()
                
                # Make sure that the same dialogue move would not be chosen for 4 times in a row
                if len(world.responses) >= 3:
                    while choice == world.responses[len(world.responses)-3].type_num and \
                          choice == world.responses[len(world.responses)-2].type_num and \
                          choice == world.responses[len(world.responses)-1].type_num:
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

                    if local_concept.userid != userid:
                        new_score = local_concept.score + 1.5     #Add the score
                        DBO_Local_Concept.update_score(last_response_concept_id, new_score) #Update the score

                        #If score exceeds, change assertion/concept type to global
                        if new_score >= SCORE_THRESHOLD:
                            DBO_Local_Concept.update_valid(last_response_concept_id, 0)
                            DBO_Concept.add_concept(Concept(local_concept.id, local_concept.first, local_concept.relation, local_concept.second))

                    #NEW RESPONSE
                    output = Move.Move(template=["Ok, let's keep going then!"], type_num=MOVE_UNKNOWN)
                
                elif "no" in coreferenced_text:
                    output = Move.Move(template=["Why not? Don't you like it or do you think it's wrong?"], type_num=MOVE_UNKNOWN)
                    world.continue_suggesting = 1
                    world.suggest_continue_count += 1

                    prev_response = world.responses[len(world.responses)-1]
                    output.move_id = prev_response.move_id
                    output.concept_id = prev_response.concept_id
                    output.blank_dictionary_move = prev_response.blank_dictionary_move
              
                else:
                    output = Move.Move(template=["Sorry, I don't understand. Please answer by yes or no"], type_num=MOVE_UNKNOWN)

            elif last_response_type_num == MOVE_UNKNOWN and world.continue_suggesting == 1:  

                if "don't like" in coreferenced_text or "dont like" in coreferenced_text:
                    # Suggest again?
                    output = suggest_again(world, coreferenced_text)

                elif "wrong" in coreferenced_text:
                    # Output using the hardcoded templates. Move should be MOVE_ANSWER? MOVE_FOLLOW_UP
                    print("NOT YET DONE")
                    prev_response = world.responses[len(world.responses)-1]

                    #Follow Up Functions
                    temp_response = get_follow_up_string(prev_response)

                    if temp_response == None:
                        # MINUS
                        #Get the entire local concept
                        local_concept = DBO_Local_Concept.get_concept_by_id(prev_response.concept_id)

                        if local_concept.userid != userid:
                            new_score = local_concept.score - 1.0     #Minus the score
                            DBO_Local_Concept.update_score(prev_response.concept_id, new_score) #Update the score

                        output = suggest_again(world, coreferenced_text)
                    else:
                        output = Move.Move(template=["Which one is wrong? " + temp_response.get_string_template()], type_num=MOVE_UNKNOWN)                                       
                        output.move_id = prev_response.move_id
                        output.concept_id = prev_response.concept_id
                        output.blank_dictionary_move = prev_response.blank_dictionary_move
                        output.concept_letter = temp_response.concept_letter

            else:
                choice = random.randint(MOVE_FEEDBACK, MOVE_HINT+1)
                output = generate_response(choice, world, [], coreferenced_text)

        elif category == CAT_COMMAND:
            # TEMP TODO: check for further commands
            choice = random.randint(MOVE_FEEDBACK, MOVE_SPECIFIC_PUMP+1)

            is_hint = "your turn" in coreferenced_text or \
                        "talk" in coreferenced_text or \
                        ("give" in coreferenced_text and "hint" in coreferenced_text)

            # is_pump = ("what" in coreferenced_text and \
            #            ("say" in coreferenced_text or "next" in coreferenced_text or "talk" in coreferenced_text))

            is_either = "help" in coreferenced_text or \
                        "stuck" in coreferenced_text
            
            is_suggesting = ("suggest" in coreferenced_text and "sentence" in coreferenced_text) or \
                            ("give" in coreferenced_text and "idea" in coreferenced_text) or \
                            "what happens next" in coreferenced_text or \
                            "trial" in coreferenced_text

            if "help me start" in coreferenced_text:
                output = generate_response(MOVE_PROMPT, world, [], coreferenced_text)
                world.add_response(output)
                return output

            # if len(world.responses) == 0:
            #     concepts = DBO_Concept.get_concept_like(txt_relation, second=txt_concept)
            if is_either:
                choice = random.randint(MOVE_GENERAL_PUMP, MOVE_HINT+1) #between suggesting and hinting
            elif is_hint:
                choice = MOVE_HINT
            # elif is_pump:
            #     choice = random.randint(MOVE_GENERAL_PUMP, MOVE_SPECIFIC_PUMP+1)
            
            elif is_suggesting:
                choice = MOVE_SUGGESTING

            output = generate_response(choice, world, [], coreferenced_text)

        else:
            output = Move.Move(template=["I don't know what to say."], type_num=MOVE_UNKNOWN)
    
    # AFTER GETTING THE TEMPLATE

    #Check if the move is suggesting, then change the variable
    if output.type_num == MOVE_SUGGESTING:
        world.continue_suggesting = 1
        world.subject_suggest = output.subject
    elif output.type_num != MOVE_UNKNOWN:
        world.continue_suggesting = 0
        world.subject_suggest = None

    world.add_response(output)
    world.add_response_type_count(output)

    #Header would be added
    feedback_add = feedback_random(output.type_num)
    if feedback_add == 1 and category == CAT_STORY:
        feedback_output = generate_response(MOVE_FEEDBACK, world, [], coreferenced_text)
        combination_response(output.type_num, world)
        output.template.insert(0, feedback_output.get_string_response() + " ")

    return output

#Note this one is when a move_code has been decided. If there is no concepts then change move_code to feedback.
def generate_response(move_code, world, remove_index, text):

    subject_list = []

    #DBO should be accessing the local concept
    DATABASE_TYPE = DBO_Concept
    if move_code == MOVE_SUGGESTING:
        DATABASE_TYPE = DBO_Local_Concept
        db_type = "local"
    else:
        DATABASE_TYPE = DBO_Concept
        db_type = "global"

    print(DATABASE_TYPE)

    choices = []
    subject = None

    if len(world.responses) > 0:
        last_response_id = world.responses[len(world.responses)-1].move_id

        print("LAST USED TEMPLATE RESPONSE: ", last_response_id)
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
            move.type_num = move_code
            break

        print("Loop count: ", index_loop)
        if index_loop > 20:
            remove_index.append(move.move_id)
            print("CHANGE MOVE")

            if world.continue_suggesting == 1: 
                return generate_response(MOVE_SPECIFIC_PUMP, world, remove_index, text)
            
            # Add for hinting, if move_code == Hinting/Suggesting?

            else:
                return generate_response(MOVE_FEEDBACK, world, remove_index, text)

    print("Generating fillable template...")
    print(str(move))

    for blank_type in move.blanks:
        print("CURRENT SUBJECTS: ", subject_list)
        subject = None # IDK????
        replace_subject_type_name = 0
        
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
                move.blank_dictionary_move[to_replace] = concept_string                
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

                        # make sure that the same subject is not used twice in one sentence.
                        # Very ugly code, need to fix
                        while decided_item.name in subject_list:
                            list_choices.pop(choice_index)

                            if len(list_choices) == 0:
                                break

                            choice_index = random.randint(0, len(list_choices))
                            decided_item = list_choices[choice_index]

                    if len(list_choices) == 0:
                        decided_item = None
                        print("AAAAaAA")
                        break

                    subject = decided_item
                    print(subject.name)
                    print(subject.type)

                    if world.continue_suggesting == 1:
                        subject = world.subject_suggest
                        print("SUBJECT SUGGEST", subject)
                        decided_node = NODE_START

                    if subject is not None and len(subject.type) > 0:
                        # decided_concept = subject.name[random.randint(0, len(subject.type))]
                        choice_index = random.randint(0, len(subject.type))
                        decided_concept = subject.type[choice_index]
                        print("SUBJECT TYPE: ", decided_concept)
                        subject_list.append(subject.name) #SUBJECT CELINA
                        replace_subject_type_name = 1
                        decided_node = NODE_START
                    else:
                        if isinstance(decided_item, Object):
                            decided_concept = decided_item.name
                            subject = decided_item
                            subject_list.append(subject) #SUBJECT CELINA
                            decided_node = NODE_START
                            print("DC", decided_concept)
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
                    list_settings_names = []
                    list_settings_names = world.settings

                    # use for the subject continuous. It "normally" gets the location 
                    # frog went to forest. 
                    # If not continous suggestion, it would get forest at the decided concept
                    # if continuous, and subject is frog then disregard this
                    if world.continue_suggesting == 0 or (world.subject_suggest is not None and world.subject_suggest.name in list_settings_names):
                        settings = world.settings

                        print("length settings", len(settings))
                        if len(settings) > 0:
                            decided_concept = settings[ran.choice(list(settings.keys()))].name
                            decided_node = NODE_END
                        else:
                            remove_index.append(move.move_id)
                            return generate_response(move_code, world, remove_index, text)

                    #else:
                    #    decided_node = NODE_START
                
                if world.continue_suggesting == 1:
                        subject = world.subject_suggest
                        print("SUBJECT SUGGEST", subject)
                        decided_node = NODE_START
            # find
            # This part looks for the concept. Example Girl went to mall. So if decided_node is NODE_END. 
            # It would look for concepts na ang second ay mall
            if decided_node == NODE_START:
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type, first=decided_concept)
            elif decided_node == NODE_END:
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type, second=decided_concept)
            elif decided_node == NODE_EITHER: #Not being used?
                usable_concepts = DATABASE_TYPE.get_concept(decided_concept, blank_type)
            else:
                usable_concepts = []

            #If there is none found, change template.
            if len(usable_concepts) == 0:
                remove_index.append(move.move_id)
                print("LP1:", loop_total)
                return generate_response(move_code, world, remove_index, text)

            while len(usable_concepts) == 0:
                loop_total += 1
                print("LP2:", loop_total)
                usable_concepts = DATABASE_TYPE.get_concept_like(blank_type)
                if loop_total > 10:
                    break
                    
            print("DECIDED CONCEPT: "+decided_concept)
            print("Num usable concept", len(usable_concepts))
            #Usable concepts for local is limited to those that are valid. Valid = 1
            remove_concept = []
            if len(usable_concepts) > 0:
                # Also check if the concept was already use here, use loops
                concept_index = random.randint(0,len(usable_concepts))
                concept = usable_concepts[concept_index]

                dbtype_concept_list = get_dbtype_concept_list(DATABASE_TYPE, world)

                #Make sure the same concept is not used again for this world.
                while concept.id in dbtype_concept_list:
                    usable_concepts.remove(concept)

                    if len(usable_concepts) == 0:
                        remove_index.append(move.move_id)
                        return generate_response(move_code, world, remove_index, text)

                    concept_index = random.randint(0,len(usable_concepts))
                    concept = usable_concepts[concept_index]
                    #print("USABLE CON2", len(usable_concepts))

                if replace_subject_type_name == 1:
                    concept.first = subject.name

                move.template[move.template.index("start")] = concept.first
                move.template[move.template.index("end")] = concept.second

                move.blank_dictionary_move["start"] = concept.first
                move.blank_dictionary_move["end"] = concept.second

                # No need to swap sa iba, this is the only one because start and end from db
                
                # Get the concept id, this is for adding the score
                move.concept_id = concept.id

                if DATABASE_TYPE == DBO_Concept:
                    world.global_concept_list.append(concept.id)
                elif DATABASE_TYPE == DBO_Local_Concept:
                    world.local_concept_list.append(concept.id)
                
                print("USED GLOBAL ASSERTIONS ID: ", world.global_concept_list)
                print("USED LOCAL ASSERTIONS ID: ", world.local_concept_list)

            else:
                print("ERROR: NO USABLE CONCEPTS decided:",decided_concept)
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)

        elif blank_type == "Object":

            if subject is None:
                charas = world.get_top_characters()
                objects = world.get_top_objects()
                list_choices = charas + objects

                if len(list_choices) > 0:
                    choice_index = random.randint(0, len(list_choices))
                    subject = list_choices[choice_index]
                    subject_list.append(subject) #SUBJECT CELINA
                else:
                    remove_index.append(move.move_id)
                    return generate_response(move_code, world, remove_index, text)

            if world.continue_suggesting == 1 and move_code == MOVE_SPECIFIC_PUMP:
                subject = world.subject_suggest

            if subject is not None:
                move.template[move.template.index("object")] = subject.id
                move.blank_dictionary_move["object"] = subject.id

        elif blank_type == "Item":

            if subject is None:
                objects = world.get_top_objects()

                if len(objects) > 0:
                    choice_index = random.randint(0, len(objects))
                    subject = objects[choice_index]
                    subject_list.append(subject) #SUBJECT CELINA
                else:
                    remove_index.append(move.move_id)
                    return generate_response(move_code, world, remove_index, text)
            
            if world.continue_suggesting == 1 and move_code == MOVE_SPECIFIC_PUMP:
                subject = world.subject_suggest

            if subject is not None:
                move.template[move.template.index("item")] = subject.id
                move.blank_dictionary_move["item"] = subject.id

        elif blank_type == "Character":
            if subject is None or not isinstance(subject, Character):
                charas = world.get_top_characters(5)
                if len(charas) > 0:
                    choice_index = random.randint(0, len(charas))
                    subject = charas[choice_index]
                    # Line 668 sa Dialogue Planner
                    # subject = charas[0]
                    #add condition here that shows na bawal ang character dito na same sa suggest subject?
                else:
                    remove_index.append(move.move_id)
                    return generate_response(move_code, world, remove_index, text)
            else:
                chara = subject
            
            if world.continue_suggesting == 1 and move_code == MOVE_SPECIFIC_PUMP:
                subject = world.subject_suggest

            if subject is not None:
                subject_list.append(subject.id) #SUBJECT CELINA
                move.template[move.template.index("character")] = subject.id
                move.blank_dictionary_move["character"] = subject.id

        elif blank_type == "inSetting":
            if subject is None:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)
            elif subject.inSetting is None:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)
            else:
                move.template[move.template.index("inSetting")] = subject.inSetting['LOC']
                move.blank_dictionary_move["inSetting"] = subject.inSetting['LOC']

        elif blank_type == "Repeat":

            if len(world.event_chain) > 0:
                move.template[move.template.index("repeat")]\
                    = to_sentence_string(world.event_chain[len(world.event_chain)-1])
                move.blank_dictionary_move["repeat"]\
                    = to_sentence_string(world.event_chain[len(world.event_chain)-1])
            else:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)

        elif blank_type == "Pronoun":
            if subject is None:
                move.template[move.template.index("pronoun")] = "it"
                move.blank_dictionary_move["pronoun"] = "it"
            else:
                if isinstance(subject, Object):
                    move.template[move.template.index("pronoun")] = "they"
                    move.blank_dictionary_move["pronoun"] = "they"
                elif subject.gender == "":
                    move.template[move.template.index("pronoun")] = "they"
                    move.blank_dictionary_move["pronoun"] = "they"
                elif subject.gender == "M":
                    move.template[move.template.index("pronoun")] = "he"
                    move.blank_dictionary_move["pronoun"] = "he"
                elif subject.gender == "F":
                    move.template[move.template.index("pronoun")] = "she"
                    move.blank_dictionary_move["pronoun"] = "she"
                else:
                    move.template[move.template.index("pronoun")] = subject.name
                    move.blank_dictionary_move["pronoun"] = subject.name

        elif blank_type == "Event":
            loop_back = len(world.event_chain)-1
            loops = 0
            while loop_back >= 0 and loops < 5:
                event = world.event_chain[loop_back]

                if event.event_type == FRAME_EVENT:
                    if event.action != "":
                        if "eventverb" in move.template:
                            move.template[move.template.index("eventverb")] = event.action
                            move.blank_dictionary_move["eventverb"] = event.action
                        if "object" in move.template:
                            move.template[move.template.index("object")] = get_subject_string(event)
                            move.blank_dictionary_move["object"] = get_subject_string(event)

                loop_back -= 1
                loops += 1

            if loop_back == -1 or loops >= 5:
                remove_index.append(move.move_id)
                return generate_response(move_code, world, remove_index, text)

    print("SUBJECTSSS: ", subject_list)    
    header_text(move_code, move, world)

    print("FINAL MOVE DECISION:")
    print(str(move))
    move.subject = subject
    return move

def feedback_random(type_num):
    if type_num == MOVE_GENERAL_PUMP or type_num == MOVE_SPECIFIC_PUMP or type_num == MOVE_HINT or type_num == MOVE_SUGGESTING:
        return random.randint(0,2)
    else:
        return -1

def combination_response(type_num, world):
    type = -1
    if type_num == MOVE_GENERAL_PUMP:
        type = 9        
    elif type_num == MOVE_SPECIFIC_PUMP:
        type = 10
    elif type_num == MOVE_HINT: 
        type = 11
    elif type_num == MOVE_SUGGESTING:
        type = 12

    world.add_combination_response_type_count(type)

def header_text(move_code, move, world):
    if move_code == MOVE_SUGGESTING:
        move.template.insert(0, "What if ")
        move.template.append("?")
    
    elif move_code == MOVE_HINT:
        elements = ["Then ", "I think ", "Hmm, I think "]
        header = random.choice(elements) 
        move.template.insert(0, header)
    
    if world.continue_suggesting == 1 and move_code == MOVE_SPECIFIC_PUMP and world.subject_suggest is not None:
        move.template.insert(0, "I don't know much about " + world.subject_suggest.name + ". Please help me learn more. ")
        move.template.append("?")

def get_dbtype_concept_list(DATABASE_TYPE, world):
    if DATABASE_TYPE == DBO_Concept:
        return world.global_concept_list
    elif DATABASE_TYPE == DBO_Local_Concept:
        return world.local_concept_list

def get_follow_up_string(prev_response):
    temp = []

    temp = DBO_Follow_Up.get_specific_follow_up_template(prev_response.move_id)
    if temp == None:
        return None

    temp.blank_dictionary = prev_response.blank_dictionary_move
    temp.split_template()
    temp.fill_blank_template()
    return temp

def suggest_again(world, coreferenced_text):
    if world.suggest_continue_count == 3:
        world.suggest_continue_count = 0
        choice = MOVE_SPECIFIC_PUMP
        output = generate_response(choice, world, [], coreferenced_text)
                
    else:
        # output = Move.Move(template=["I don't know much about " + world.subject_suggest.name + ". Tell me more about " + world.subject_suggest.name + " ."], type_num=MOVE_SPECIFIC_PUMP)
        choice = MOVE_SUGGESTING
        output = generate_response(choice, world, [], coreferenced_text)
    
    return output