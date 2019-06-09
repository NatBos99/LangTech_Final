#!/usr/bin/python3
import sys
import requests
import re
import spacy
from XofYisZ import *

nlp = spacy.load('en')

#Finds X of Y, returns string 'no results' if no results found
def get_results(xstring, ystring):
	url = 'https://www.wikidata.org/w/api.php'
	Xparams = {'action':'wbsearchentities',
			'language':'en',
			'format':'json',
			'type':'property'}

	Yparams = {'action':'wbsearchentities',
			'language':'en',
			'format':'json',}


	Yparams['search'] = ystring
	Yjson = requests.get(url,Yparams).json()
	Xparams['search'] = xstring
	Xjson = requests.get(url,Xparams).json()

	#loop through all the search results of X and Y
	for result in Yjson['search']:
		y = result['id']
		for result in Xjson['search']:
			x = result['id']
			data = get_data(x,y)
			if data['results']['bindings'] != []:
				#print(data)
				return data
	return ('no results')

#Extracts data from wikidata API
def get_data(x, y):
	url2 = 'https://query.wikidata.org/sparql'
	query='''
	SELECT  ?itemLabel
	WHERE
	{{
		wd:{} wdt:{} ?item.
		SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
	}}'''.format(y,x)

	data = requests.get(url2, params={'query': query, 'format': 'json'}).json()
	return data

#Extracts data and puts it into a list
def extract_answer(data):
	mylist = []
	for item in data['results']['bindings']:
		for var in item :
			mylist.append(item[var]['value'])
	return mylist

#Can print list answers in a single line
def print_answer(answers):
	for answer in answers:
			print(answer, end='\t', flush=True)
	print('')
	
########################################################################
def isCase_1(question):	
	if question[0:2] == 'Is':
		return True
	elif question[0:3] == 'Are':
		return True
	elif question[0:3] == 'Was':
		return True
	elif question[0:4] == 'Were':
		return True
	elif question[0:4] == 'Does':
		return True
	elif question[0:3] == 'Did':
		return True
	else:
		return False	
	
def isCase_2(question):
	return False
		
def isCase_3(question):
	return False

def isCase_4(question):
	return False
	
########################################################################

def findAnswerCase_1(parse):
	finalAnswer = []
	questionAnswer = []
	
	#Test Case: Is Donda West the mother of Kanye West
	questionAnswer.append('Donda West')
	xstring = 'mother'
	ystring = 'Kanye West'
	
	data = get_results(xstring,ystring)
	#fail Case
	if data == 'no results':
		finalAnswer.append('Could not find answer')
		return finalAnswer
	else:
		if questionAnswer == extract_answer(data):
			finalAnswer.append('Yes')
		else:
			finalAnswer.append('No')
		return finalAnswer	
		
def findAnswerCase_2(parse):
	print('Incomplete Code') 

def findAnswerCase_3(parse):
	print('Incomplete Code') 

def findAnswerCase_4(parse):
	return find_x_of_y_is_z(parse)
	
########################################################################

def find_answer(question):
	
	parse = nlp(question)
	
	for w in parse:
		print("\t \t".join((w.text, w.lemma_, w.pos_, w.tag_, w.dep_,w.head.lemma_)))

	answer = []
	#Yes/No Questions
	if isCase_1(question) == True:
		answer = findAnswerCase_1(parse)
	
	#Highest/Lowest Questions
	elif isCase_2(question) == True:
		answer = findAnswerCase_2(parse)
		
	#Count Questions
	elif isCase_3(question) == True:
		answer = findAnswerCase_3(parse)
	
	#Fail Case, check for x of y is z questions (What/Who/Where/When/How Questions)
	else:
		answer = findAnswerCase_4(parse)
		
	print(answer)
		

def main (argv):
	for sentence in sys.stdin:
		find_answer(sentence)

if __name__ == "__main__":
	main(sys.argv)
