#!/usr/bin/python3

import sys
import requests
import re
import spacy

def find_compound(parsed, h, x, mustBeNoun):
    # Find any words that should be part of x but are not automatically found
    compound = ""
    abort = 0
    xText = x.lemma_
    if (x.pos_ == "VERB" and mustBeNoun):
        xText = verb_to_noun(xText)
    for i in parsed:
        if i == x:
            if (abort == 0):
                return compound + xText
            else:
                return ""
        if (i.pos_ == "PRON"):
            abort = 1 # If we find, for example, "What x is the y of z", we treat "What x" as if "x" is not there. "What" would be removed under normal circumstances anyway
        elif (i.dep_ == "compound" or i.dep_ == "amod"):
            compound += i.lemma_
            compound += " "
        elif (i.dep_ == "prep" and i.lemma_ == "of" and not i == h):
            compound += i.head.lemma_
            compound += " "
            compound += i.lemma_
            compound += " "
        else:
            compound = ""
            abort = 0

def verb_to_noun(verb):
    if (verb == "bear"):
        return "birth"
    if (verb == "die"):
        return "death"
    return verb

def find_how_xyz_format(parsed, h, iteration):
    #When was y x(verb)?

    #Find x
    xObject = h.head.head
    x = find_compound(parsed, h, xObject, True) #Find anything that might need to be included in x
    if (iteration == 0):
        x = "cause of "+x
    if (iteration == 1):
        x = "manner of "+x

    #Find y
    y = ""
    for i in parsed:
        if (i.head == xObject and i.dep_ == "nsubj"):
            yObject = i
            y = find_compound(parsed, h, yObject, True) #Find anything that might need to be included in y
            break

    #z cannot be present in these kinds of sentences
    z = ""

    return [x, y, z]

def find_when_xyz_format(parsed, h):
    #When was y x(verb)?

    #Find x
    xObject = h.head.head
    x = find_compound(parsed, h, xObject, True) #Find anything that might need to be included in x
    x = "date of "+x

    #Find y
    y = ""
    for i in parsed:
        if (i.head == xObject and i.dep_ == "nsubj"):
            yObject = i
            y = find_compound(parsed, h, yObject, True) #Find anything that might need to be included in y
            break

    #z cannot be present in these kinds of sentences
    z = ""

    return [x, y, z]

def find_standard_xyz_format(parsed, h, propDate):
    #Find x
    xObject = h.head
    x = ""
    if (not xObject.pos_ == "PRON"):
        x = find_compound(parsed, h, xObject, False) #Find anything that might need to be included in x
        if(propDate):
            x = "date of" + x

    #Find y
    y = ""
    for i in parsed:
        if (i.head == h and not i.pos_ == "PRON"):
            yObject = i
            y = find_compound(parsed, h, yObject, False) #Find anything that might need to be included in y
            break

    #Find z
    possibleIs = xObject.head
    z = ""
    if (possibleIs.lemma_ == "be"):
        for i in parsed:
            if ((i.pos_ == "NOUN" or i.pos_ == "PROPN") and i.head == possibleIs and not i == xObject):
                zObject = i
                z = find_compound(parsed, h, zObject, False) #Find anything that might need to be included in z
                break
    return [x, y, z]

def find_xyz_answer(x, y, z):
    answer = ""
    depth = 5 #Increase for better chance of finding obscure answers, decrease for slightly better performance
    xId = get_id(x, "property")
    yId = get_id(y, "object")
    zId = get_id(z, "object")
    for numi, i in enumerate(xId):
        if (numi == depth):
            break
        for numj, j in enumerate(yId):
            if (numj == depth):
                break
            for numk, k in enumerate(zId):
                if (numk == depth):
                    break
                if (not ((i == "" and j == "") or (i == "" and k == "") or (j == "" and k == ""))):
                    query = construct_query_xyz(i, j, k)
                    print(query)
                    if (not query == "Nothing"):
                        answer = find_answer_to_query(query)
                        if (not answer == ""):
                            return answer
    return "No answer was found"

def find_x_of_y_is_z(parsed):
    for numh in range(len(parsed)-1, -1, -1):
        h = parsed[numh]
        print (h.lemma_)
        if (h.dep_ == "prep" and h.lemma_ == "of"):
            li = find_standard_xyz_format(parsed, h, False)
            x = li[0]
            y = li[1]
            z = li[2]

            print ("the %s of %s is %s" %(x, y, z))
            answer = find_xyz_answer(x, y, z)
            if (not answer == "No answer was found"):
                return answer

        if (h.head.pos_ == "VERB" and h.lemma_ == "when"):
            print ("Hoera")
            if (h.head.dep_ == "ROOT"):
                li = find_standard_xyz_format(parsed, h, False)
                x = li[0]
                y = li[1]
                z = li[2]

                print ("the %s of %s is %s" %(x, y, z))
                answer = find_xyz_answer(x, y, z)
                if (not answer == "No answer was found"):
                    return answer

                li = find_standard_xyz_format(parsed, h, True)
                x = li[0]
                y = li[1]
                z = li[2]

                print ("the %s of %s is %s" %(x, y, z))
                answer = find_xyz_answer(x, y, z)
                if (not answer == "No answer was found"):
                    return answer

            li = find_when_xyz_format(parsed, h)
            x = li[0]
            y = li[1]
            z = li[2]

            print ("the %s of %s is %s" %(x, y, z))
            answer = find_xyz_answer(x, y, z)
            if (not answer == "No answer was found"):
                return answer

    if (h.head.pos_ == "VERB" and h.lemma_ == "how"):
        for i in range(0, 1, 2):
            li = find_how_xyz_format(parsed, h, i)
            x = li[0]
            y = li[1]
            z = li[2]

            print ("the %s of %s is %s" %(x, y, z))
            answer = find_xyz_answer(x, y, z)
            if (not answer == "No answer was found"):
                return answer

    return "No answer was found"

def add_hardcoded_ids(ret, string, typ):
    print(string)
    if (string == "member" and typ == "property"):
        ret.append("P527") #Has part
    if (string == "real name" and typ == "property"):
        ret.append("P1477") #Birth name

def get_id(string, idType):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities',
                'language':'en',
                'format':'json'
                }
    if idType == 'property':
        params['type'] = 'property'

    params['search'] = string.rstrip()
    json = requests.get(url,params).json()
    ret = []
    add_hardcoded_ids(ret, string, idType)
    try:
        for i in json['search']:
            print("{}\t{}\t{}".format(i['id'],i['label'],i['description']))
            ret.append(i['id'])
        ret.append("")
        return ret
    except KeyError:
        ret.append("")
        return ret

def construct_query_xyz(x, y, z):
    if ((x == "" and y == "") or (x == "" and z == "") or (y == "" and z == "")):
        return "Nothing"
    propQuery = 0
    if (x == ""):
        x = "?answer"
        propQuery = 1
    else:
        x = "wdt:"+x

    if (y == ""):
        y = "?answer"
    else:
        y = "wd:"+y

    if (z == ""):
        z = "?answer"
    else:
        z = "wd:"+z
    if(propQuery):
        query = '''
            SELECT DISTINCT ?propLabel
                Where{
                hint:Query hint:optimizer "None" .
                %s %s %s .
                ?prop wikibase:directClaim ?answer .
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en" .
                }
            }
            ''' %(y, x, z)
    else:
        query = '''
            SELECT DISTINCT ?answerLabel
                Where{
                %s %s %s .
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en" .
                }
            }
            ''' %(y, x, z)
    return query

def find_answer_to_query(query):
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format' : 'json'}).json()
    answer = ""
    for item in data['results']['bindings']:
        for var in item:
            #print(item[var]['value'])
            answer += item[var]['value']
            answer += "\n"
    answer = answer.strip("\n")
    return answer
