from src.run import extract_info, new_world, get_unkown_word
from src.dialoguemanager.DialoguePlanner import *
from flask import Flask
from flask import jsonify
from flask import request
from flask import json
import datetime
import requests
import re
from src.dialoguemanager.story_generation import generate_basic_story, generate_collated_story
from src.inputprocessor.infoextraction import getCategory, CAT_STORY
from src.db import DBO_User, User
#import logging
app = Flask(__name__)

#gunicorn_error_logger = logging.getLogger('gunicorn.error')
#app.logger.handlers.extend(gunicorn_error_logger.handlers)
#app.logger.setLevel(logging.DEBUG)
#app.logger.debug('this will show in the log')

storyId = -1
output = "Hello, I am ORSEN. Let's start."
retrieved = None
nIR = {"I can't hear you", "Sorry. What did you say again?", "Okay"}
tts = "Sorry. What did you say again?"
dt = "Sorry. What did you say again?"

focus = None

manwal_kawnt = 0
MAKSIMUM_KAWNT = 5
endstory = False
endstorygen = False
endconvo = False

story_list = []
turn_count = 0
userid = -1
username = ""
secret_code = ""

#FOR FILES
path ="D:/Desktop/Jilyan/Academics/College/THESIS/Conversation Logs"
date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

def main_intent():
	return None


@app.route('/', methods=["GET","POST"])
def home():
	print("HOME")
	return jsonify({"Page":"Home"})
	
@app.route('/orsen', methods=["POST"])
def orsen():
	global manwal_kawnt, storyId, endstory, endstorygen, story_list, turn_count, userid, username, secret_code
	
	#print(json.dumps(request.get_json()))
	requestJson = request.get_json()
	
	focus = requestJson["inputs"][0]#["rawInputs"][0]["query"]
	#print(focus["intent"])
    
    #FOR FILES - OPEN
	fileWriter = open(path+ "/" + date+".txt", "a")
	
	#When the app invocation starts, create storyid and greet the user and reset reprompt count
	if focus["intent"] == "actions.intent.MAIN":
		storyId = storyId + 1
		print("STORY ID ",storyId)
		new_world(storyId)
		#reset reprompt count
		manwal_kawnt = 0
		turn_count = turn_count + 1
		#greet user (app.ask)
		data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Hi! What's your name?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
        
		#FOR FILES
		fileWriter.write("ORSEN: Hi! What's your name?" + "\n")

	elif focus["intent"] == "actions.intent.GIVE_IDEA_ORSEN":
		data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Okay, I will give you a hint"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
        
        #FOR FILES
		fileWriter.write("ORSEN: Okay, I will give you a hint" + "\n")
	
	
	#When there is no input: ask the user (prompt from model) until maximum count is reached 
	elif focus["intent"] == "actions.intent.NO_INPUT":
		#increment reprompt count
		manwal_kawnt = manwal_kawnt + 1
		#app termination when maximum reprompt count is reached
		if manwal_kawnt == MAKSIMUM_KAWNT:
			data = {"expectUserResponse": False, "finalResponse": {"speechResponse": {"textToSpeech": "Okay. Goodbye"}}}
            
			#FOR FILES - CLOSE
			fileWriter.write("ORSEN: Okay. Goodbye" + "\n")
			fileWriter.close()

		#reprompt user
		else:
			#get the reprompt
			retrieved = retrieve_output("", storyId)
			
			if retrieved.type_num == MOVE_HINT:
				extract_info(userid, retrieved.get_string_response())
	
			output_reply = retrieved.get_string_response()
			#reprompt user
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":""+output_reply+""}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
	
	elif turn_count == 1:
		rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
		turn_count = turn_count + 1
		username = str(rawTextQuery).split()
		username = username[len(username)-1].lower()
		data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Do we have a secret code?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
		
	elif turn_count == 2:
		rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
		if str(rawTextQuery).lower() == "yes":
			turn_count = turn_count + 2
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"I see, can you tell me what it is?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
		else:
			turn_count = turn_count + 1
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"I see, let's make one then. So what will it be?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
		
	elif turn_count == 3:
		rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
		if str(rawTextQuery) != "":
			secret_code = str(rawTextQuery).split()
			secret_code = secret_code[len(secret_code)-1].lower()
			turn_count = turn_count + 2
			# add to DB
			user = User.User(-1, username, secret_code)
			DBO_User.add_user(user)
			# get user id
			userid = DBO_User.get_user_id(username, secret_code)
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Yey, a new friend! Let's make a story. You go first " + username + "."}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}

	elif turn_count == 4:
		rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
		secret_code = str(rawTextQuery).split()
		secret_code = secret_code[len(secret_code)-1].lower()
		# check if username and secret code match in db

		userid = DBO_User.get_user_id(username, secret_code)
		print("user id")
		print(userid)
		if userid != -1:
			turn_count = turn_count + 1
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Oh, you remembered " + username + "! Okay, let's make a story then. you start!"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
		else:
			print("try again")
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Hmm, I don't think that was our secret code. Why don't you give it another try " + username + "?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}

	#When there is input, simply pass to model and get reply
	else:
		rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
	
		manwal_kawnt =0
		# userId = requestJson["user"]["userId"] # some really long id
		data = {}
		genstory = ""
	
		#print(rawTextQuery + " ["+userId+"]")

		if endstory:
			rawTextQuery = requestJson["inputs"][0]["rawInputs"][0]["query"]
			#If user wants to create another story, create new story and reset reprompt counts
			# if user wants to hear the whole story
			if (not endstorygen) and (rawTextQuery == "yes" or rawTextQuery == "yes." or rawTextQuery == "sure" or rawTextQuery == "sure." or rawTextQuery == "yeah" or rawTextQuery == "yeah."):
				#(edit-addhearstory-p2)swapped the contents of first and this condition
				output_reply = generate_collated_story(server.get_world(storyId))
				print("-----======= GENERATED STORY =======------")
				print(output_reply)
				data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":""+output_reply+""+". Do you want to create another story?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
				endstorygen = True
                
				#FOR FILES
				fileWriter.write("CHILD: "+ rawTextQuery + "\n")
				fileWriter.write("ORSEN: "+ output_reply + "Do you want to create another story?" + "\n")
			
			# user does not want to hear the full story
			elif not endstorygen:
				#(edit-addhearstory-p1) changed prompt from 'hear story' to 'create story'
				data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Okay. Do you want to create another story?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
				endstorygen = True
                
				#FOR FILES
				fileWriter.write("CHILD: "+ rawTextQuery + "\n")
				fileWriter.write("ORSEN: Okay. Do you want to create another story?" + "\n")
				
			# user wants to create a new story
			elif endstorygen and (rawTextQuery == "yes" or rawTextQuery == "yes." or rawTextQuery == "sure" or rawTextQuery == "sure." or rawTextQuery == "yeah" or rawTextQuery == "yeah."):
				#(edit-addhearstory-p2) swapped the contents of first and this condition
				data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Okay then, Let's create a story. You start"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
				manwal_kawnt = 0
				storyId = storyId + 1
				print("STORY ID ",storyId)
				new_world(storyId)
				endstorygen = False
				endstory = False
				story_list = []
				turn_count = 0
                
				#FOR FILES
				fileWriter.write("CHILD: "+ rawTextQuery + "\n")
				fileWriter.write("ORSEN: Okay then, Let's create a story. You start" + "\n")
				
			#If the user does not want to create a new story 
			else:
				#inserted, generatestory
				data = {"expectUserResponse": False, "finalResponse": {"speechResponse": {"textToSpeech": "Thank you. Goodbye"}}}
				endstorygen = False
				endstory = False
				story_list = []
				turn_count = 0
                
				#FOR FILES - CLOSE
				fileWriter.write("CHILD: "+ rawTextQuery + "\n")
				fileWriter.write("ORSEN: Thank you. Goodbye" + "\n")
				fileWriter.close()
				
		#when the user says they want to stop telling the story
		elif rawTextQuery == "bye" or rawTextQuery == "the end" or rawTextQuery == "the end.":
			#(edit-addhearstory-p1) changed the prompt from 'create another story' to 'hear full story'
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":"Wow. Thanks for the story. Do you want to hear the full story?"}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
			endstory = True
            
			#FOR FILES
			fileWriter.write("CHILD: "+ rawTextQuery + "\n")
			fileWriter.write("ORSEN: Wow. Thanks for the story. Do you want to hear the full story?" + "\n")
            
		else:
			result = None
			story_list.append(rawTextQuery)
			# if the reply is a story, then extract info and add in story. If not, then don't add
			if getCategory(rawTextQuery) == CAT_STORY:
				# you can pass user id here
				story_list[len(story_list)-1] = extract_info(userid, story_list)
				result = get_unkown_word()
			
			if result != None:
				output_reply = "Can you tell me more about " + result + "?"

			else:
				#dialogue
				#get the dialogue regardless of type
				retrieved = retrieve_output(rawTextQuery, storyId)

				if retrieved.type_num == MOVE_HINT:
					extract_info(userid, retrieved.get_string_response())

				output_reply = retrieved.get_string_response()
				
			data = {"conversationToken":"{\"state\":null,\"data\":{}}","expectUserResponse":True,"expectedInputs":[{"inputPrompt":{"initialPrompts":[{"textToSpeech":""+output_reply+""}],"noInputPrompts":[{"textToSpeech":tts,"displayText":dt}]},"possibleIntents":[{"intent":"actions.intent.TEXT"}]}]}
	
			print("I: ", rawTextQuery)
			print("O: ", output_reply)
			#print(datetime.now())
			#path ="C:/Users/ruby/Desktop/Thesis/ORSEN/Conversation Logs"
			#date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
			#fileWriter = open(path+ "/" + date+".txt", "w")
			fileWriter.write("Child: " + rawTextQuery + "\n")
			fileWriter.write("ORSEN: " + output_reply + "\n")
			#fileWriter.close()
	
	
	#if expectedUserResponse is false, change storyId
	
	return jsonify(data)

if __name__ == '__main__':
    app.run(debug = True)