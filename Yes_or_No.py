#!/usr/bin/python3
import sys
import requests
import re
import spacy

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

    try:
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
                    return data
    except Exception:
        return ('no results')

def get_xstring_data(ystring, zstring):
    url3 = 'https://www.wikidata.org/w/api.php'
    Yparams = {'action':'wbsearchentities',
            'language':'en',
            'format':'json',}

    Zparams = {'action':'wbsearchentities',
            'language':'en',
            'format':'json',}

    try:
        Zparams['search'] = zstring
        Zjson = requests.get(url3,Zparams).json()
        Yparams['search'] = ystring
        Yjson = requests.get(url3,Yparams).json()

        #loop through all the search results of Y and Z
        for result in Yjson['search']:
            y = result['id']
            for result in Zjson['search']:
                z = result['id']
                data = get_property_data(y,z)
                if data['results']['bindings'] != []:
                    return data
    except Exception:
        return ('no results')


def get_property_data(y,z):
    url4 = 'https://query.wikidata.org/sparql'
    query='''
    SELECT  ?itemLabel
    WHERE
    {{
        wd:{} ?itemLabel wd:{}.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}'''.format(y,z)

    data = requests.get(url4, params={'query': query, 'format': 'json'}).json()
    return data

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
    try:
        mylist = []
        for item in data['results']['bindings']:
            for var in item :
                mylist.append(item[var]['value'])
        return mylist
    except Exception:
        return None

#Can print list answers in a single line
def print_answer(answers):
    for answer in answers:
            print(answer, end='\t', flush=True)
    print('')

########################################################################

def check_be_z_the_x_of_y(parse):
    for w in parse:
        if w.dep_== "pobj":
            return True
    return False

def find_string(w, parse, string):
    for x in parse:
        if x.dep_ == "compound" and x.head.lemma_ == w.lemma_ :
            if string == "":
                string = x.text
            else:
                string += " " + x.text
        elif x.text == w.text and string == "":
            string = w.text
        else:
            if x.text == w.text:
                string += " " + w.text
    return string

########################################################################

def find_do_z_x_y(parse):
    xstring = ""; ystring = ""; zstring = "";
    for w in parse:
        #Find ystring
        if w.dep_ == "nsubj" :
            zstring = find_string(w, parse, zstring)

        #Find xstring
        if w.dep_ == "ROOT" and (w.pos_ == "VERB" or w.pos_ == "NOUN"):
            xstring = w.text
            #Find preposition if any
            for x in w.subtree:
                if x.dep_ == "prep" and x.head.lemma_ == w.lemma_:
                    xstring += " " + x.text
        #Find zstring
        if w.dep_ == "pobj" or w.dep_=="dobj":
            ystring = find_string(w, parse, ystring)

    return (xstring, ystring, zstring)

def find_be_z_the_x_of_y(parse,question):
    xstring = ""; ystring = ""; zstring = "";

    if parse[0].text == 'Is':
        m = re.search('Is (.*) the (.*) of (.*)?', question)
    if parse[0].text == 'Are':
        m = re.search('Are (.*) the (.*) of (.*)?', question)
    if parse[0].text == 'Was':
        m = re.search('Was (.*) the (.*) of (.*)?', question)
    if parse[0].text == 'Were':
        m = re.search('Were (.*) the (.*) of (.*)?', question)

    xstring = m.group(2)
    ystring = m.group(3)
    zstring = m.group(1)
    ystring = ystring.replace("?","")

    return (xstring, ystring, zstring)


def find_be_y_z(parse):
    xstring = ""; ystring = ""; zstring = "";
    xstring = "is a"
    for w in parse:
        #find ystring
        if w.dep_ == "nsubj":
            ystring = find_string(w, parse, ystring)
        #find zstring
        if (w.dep_ == "appos" or w.dep_ =="attr" or w.dep_ == "acomp"):
            zstring = find_string(w, parse, zstring)
    data = get_xstring_data(ystring, zstring)
    myList = extract_answer(data)
    xstring = myList[0]
    return xstring, ystring, zstring

########################################################################

def yes_no_questions_get_x_y_z(parse,question):
    xstring = ""; ystring = ""; zstring = "";

    #Do Z X Y? (Did B. B. King influence Jimi Hendrix?)
    if parse[0].lemma_ == "do":
        xstring, ystring, zstring = find_do_z_x_y(parse)

    #Be Z the X of Y? (Is Donda West the mother of Kanye West)
    elif check_be_z_the_x_of_y(parse) == True:
        xstring, ystring, zstring = find_be_z_the_x_of_y(parse,question)

    #Be Z Y? (Is Shakira a model, Is Michael Jackson alive)
    else:
        xstring, ystring, zstring = find_be_y_z(parse)

    return xstring, ystring, zstring

########################################################################
def isCase_1(parse):
    if parse[0].lemma_ == 'be' or parse[0].lemma_ == 'do':
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

def findAnswerCase_1(parse,question):
    finalAnswer = []
    candidateAnswer = []
    xstring, ystring, zstring = yes_no_questions_get_x_y_z(parse,question)
    print("x: " + xstring)
    print("y: " + ystring)
    print("z: " + zstring)
    candidateAnswer.append(zstring)
    data = get_results(xstring,ystring)
    listAnswers = extract_answer(data)

    #fail Case
    if data == 'no results':
        finalAnswer.append('Could not find answer')
        return finalAnswer
    else:
        if zstring in listAnswers:
            finalAnswer.append('Yes')
        elif candidateAnswer == extract_answer(data):
            finalAnswer.append('Yes')
        else:
            finalAnswer.append('No')
        return finalAnswer

def findAnswerCase_2(parse):
    print('Incomplete Code')

def findAnswerCase_3(parse):
    print('Incomplete Code')

def findAnswerCase_4(parse):
    print('Incomplete Code')

########################################################################

def find_answer(question):

    parse = nlp(question)

    for w in parse:
        print("\t \t".join((w.text, w.lemma_, w.pos_, w.tag_, w.dep_,w.head.lemma_)))

    answer = []
    #Yes/No Questions
    if isCase_1(parse) == True:
        answer = findAnswerCase_1(parse,question)

    #Highest/Lowest Questions
    elif isCase_2(question) == True:
        answer = findAnswerCase_2(parse)

    #Count Questions
    elif isCase_3(question) == True:
        answer = findAnswerCase_3(parse)

    #What/Who/Where/When/How Questions
    elif isCase_4(question) == True:
        answer = findAnswerCase_4(parse)

    #Fail Case
    else:
        answer.append('Could not find answer')

    print_answer(answer)


def main (argv):
    for sentence in sys.stdin:
        find_answer(sentence)

if __name__ == "__main__":
    main(sys.argv)
