import string
import re
import sys
import requests
import spacy


def find(string, isProp):
	if isProp:
		params = {'action':'wbsearchentities', 'language':'en', 'format':'json', 'type':'property'}
	else:
		params = {'action':'wbsearchentities', 'language':'en', 'format':'json'}	

	url = 'https://www.wikidata.org/w/api.php'

	params['search'] = string.rstrip()
	json = requests.get(url,params).json()

	if len(json['search']) > 0:
		result = json['search'][0]
		return result['id']

def parse(sentence, line):

	m = re.search(sentence, line)

	first = m.group(1)
	second = m.group(2)

	nlp=spacy.load('en')
	result=nlp(first)
	for b in result:
		if b.dep_ == "nsubj":
			subject=[]
			for s in b.subtree:
				if s.dep_ == "compound" or s.dep_ != "det" :
					subject.append(s.text)
					break
		elif b.dep_ == "pobj":
			subject=[]
			for d in b.subtree:
				if d.dep_ == "compound" or d.dep_ != "det" :
					subject.append(d.text)
					break

		elif b.dep_ == "dobj":
			subject=[]
			for c in b.subtree:
				if c.dep_ == "compound" or c.dep_ != "det" :
					subject.append(c.text)
					break



	result2=nlp(second)
	subject2=[]
	flag=0
	for d in result2:
		if d.dep_ != "acl" :
			if d.dep_ == "acl" :
				flag=1
				break
			
			if d.pos_ == "VERB" :
				flag=1
				break

			if d.pos_ != "DET" :
				subject2.append(d.text)

		else :
			flag=1
			break
	if flag==1 :
		flag=0

	statement = ""


	propid = find(" ".join(subject), True)
	entityid = find(" ".join(subject2), False)
	
	query = '''SELECT ?itemLabel WHERE {
	SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
	wd:'''+entityid+''' wdt:'''+propid+''' ?item.''' + statement + '''
	}LIMIT 100'''

	url = 'https://query.wikidata.org/sparql';

	data = requests.get(url, params={'query': query, 'format': 'json'}).json();
	if len(data['results']['bindings']) == 0:
		raise ValueError
	else:
		for item in data['results']['bindings']:
				for var in item :
					print('{}'.format(item[var]['value']))



for line in sys.stdin:
	line=line.replace("?","")
	sentence = '(.*) of (.*)'

	try:
		parse(sentence, line)
	except Exception:
		print("No answer was found, Please rephrase the question")
	
