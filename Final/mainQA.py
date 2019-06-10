#!/usr/bin/python3
import sys
import requests
import re
import spacy

nlp = spacy.load('en_core_web_md')

url = 'https://query.wikidata.org/sparql'
api_url = 'https://www.wikidata.org/w/api.php'

permutation = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2),
               (2, 2)]
count_questions_properties = ['P31', 'P279', 'P361', 'P527', 'P2670']


# TO BE REMOVED LATER!!!

# Finds X of Y, returns string 'no results' if no results found
def get_results(xstring, ystring):
    Xparams = {'action': 'wbsearchentities',
               'language': 'en',
               'format': 'json',
               'type': 'property'}

    Yparams = {'action': 'wbsearchentities',
               'language': 'en',
               'format': 'json'}

    Yparams['search'] = ystring
    Yjson = requests.get(api_url, Yparams).json()
    Xparams['search'] = xstring
    Xjson = requests.get(api_url, Xparams).json()

    # loop through all the search results of X and Y
    for result in Yjson['search']:
        y = result['id']
        for result in Xjson['search']:
            x = result['id']
            data = get_data(x, y)
            if data['results']['bindings'] != []:
                print(data)
                return data
    return None


# Extracts data from wikidata API
def get_data(x, y):
    query = '''
    SELECT  ?itemLabel
    WHERE
    {{
        wd:{} wdt:{} ?item.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}'''.format(y, x)

    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data


# Extracts data and puts it into a list
def extract_answer(data):
    mylist = []
    for item in data['results']['bindings']:
        for var in item:
            mylist.append(item[var]['value'])
    return mylist


def get_id(string, idType):
    params = {'action': 'wbsearchentities',
              'language': 'en',
              'format': 'json'
              }
    if idType == 'property':
        params['type'] = 'property'

    params['search'] = string.rstrip()
    json = requests.get(api_url, params).json()
    ret = []
    add_hardcoded_ids(ret, string, idType)
    try:
        for i in json['search']:
            print("{}\t{}\t{}".format(i['id'], i['label'], i['description']))
            ret.append(i['id'])
        ret.append("")
        return ret
    except KeyError:
        ret.append("")
        return ret


def get_xstring_data(ystring, zstring):
    url3 = api_url
    Yparams = {'action': 'wbsearchentities',
               'language': 'en',
               'format': 'json'
               }

    Zparams = {'action': 'wbsearchentities',
               'language': 'en',
               'format': 'json'
               }

    try:
        Zparams['search'] = zstring
        Zjson = requests.get(url3, Zparams).json()
        Yparams['search'] = ystring
        Yjson = requests.get(url3, Yparams).json()

        # loop through all the search results of Y and Z
        for result in Yjson['search']:
            y = result['id']
            for result in Zjson['search']:
                z = result['id']
                data = get_property_data(y, z)
                if data['results']['bindings'] != []:
                    return data
    except Exception:
        return ('no results')


########################################################################

# Sends a request to the wikidata api, retrieving an entity of a given name
def find_entity(entity, index):
    entity.replace("_", " ")
    params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    params['search'] = entity.rstrip()
    json = requests.get(api_url, params).json()
    return json['search'][index]


# Sends a request to the wikidata api, retrieving a property of a given name
def find_property(property, index):
    property.replace("_", " ")
    params = {'action': 'wbsearchentities',
              'language': 'en',
              'format': 'json',
              'type': 'property'}
    params['search'] = property.rstrip()
    json = requests.get(api_url, params).json()
    return json['search'][index]


########################################################################

def check_be_z_the_x_of_y(parse):
    for w in parse:
        if w.dep_ == "pobj":
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
    xstring, ystring, zstring = "", "", ""
    for w in parse:
        # Find ystring
        if w.dep_ == "nsubj":
            zstring = find_string(w, parse, zstring)

        # Find xstring
        if w.dep_ == "ROOT" and (w.pos_ == "VERB" or w.pos_ == "NOUN"):
            xstring = w.text
            # Find preposition if any
            for x in w.subtree:
                if x.dep_ == "prep" and x.head.lemma_ == w.lemma_:
                    xstring += " " + x.text
        # Find zstring
        if w.dep_ == "pobj" or w.dep_ == "dobj":
            ystring = find_string(w, parse, ystring)

    return (xstring, ystring, zstring)


def find_be_z_the_x_of_y(parse, question):
    xstring, ystring, zstring = "", "", ""

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
    ystring = ystring.replace("?", "")

    return (xstring, ystring, zstring)


def find_be_y_z(parse):
    xstring, ystring, zstring = "", "", ""
    xstring = "is a"
    for w in parse:
        # find ystring
        if w.dep_ == "nsubj":
            ystring = find_string(w, parse, ystring)
        # find zstring
        if (w.dep_ == "appos" or w.dep_ == "attr" or w.dep_ == "acomp"):
            zstring = find_string(w, parse, zstring)
    data = get_xstring_data(ystring, zstring)
    myList = extract_answer(data)
    xstring = myList[0]
    return xstring, ystring, zstring


########################################################################

def count_questions_get_x_and_y(parse):
    x = ""
    y = ""
    for token in parse:
        if token.tag_ == "NNS" and y == "":
            x = token.lemma_
            if token.dep_ == "compound":
                x += "_" + token.head.lemma_
        elif x != "" and (token.tag_ == "NN" or token.tag_ == "NNS"):
            y = token.lemma_
            if token.dep_ == "compound":
                y += "_" + token.head.lemma_
            break
    return x, y


# Highest lowest first last question
def highest_lowest_questions_get_x_and_y(parse):
    x = ""
    y = ""
    for token in parse:
        if token.pos_ == "ADJ":
            x = token.text
            x += "_" + token.head.lemma_
        elif token.dep_ == "pobj" and (token.tag_ == "NN" or token.tag_ == "NNS"):
            y = token.lemma_
            if token.dep_ == "compound":
                y += "_" + token.head.lemma_
            break
    return x, y


def find_how_xyz_format(parsed, h, iteration):
    

    # Find x
    xObject = h.head.head
    x = find_compound(parsed, h, xObject, True)  # Find anything that might need to be included in x
    if (iteration == 0):
        x = "cause of "+x
    if (iteration == 1):
        x = "manner of "+x

    # Find y
    y = ""
    for i in parsed:
        if (i.head == xObject and i.dep_ == "nsubj"):
            yObject = i
            y = find_compound(parsed, h, yObject, True)  # Find anything that might need to be included in y
            break

    # z cannot be present in these kinds of sentences
    z = ""

    return [x, y, z]


def find_when_xyz_format(parsed, h):
    # When was y x(verb)?

    # Find x
    xObject = h.head.head
    x = find_compound(parsed, h, xObject, True)  # Find anything that might need to be included in x
    x = "date of "+x

    # Find y
    y = ""
    for i in parsed:
        if (i.head == xObject and i.dep_ == "nsubj"):
            yObject = i
            y = find_compound(parsed, h, yObject, True)  # Find anything that might need to be included in y
            break

    # z cannot be present in these kinds of sentences
    z = ""

    return [x, y, z]

def find_possessive_xyz_format(parsed, h, propDate):
    # Find x
    xObject = h.head.head
    x = ""
    if (not xObject.pos_ == "PRON"):
        x = find_compound(parsed, h, xObject, False)  # Find anything that might need to be included in x
        if(propDate):
            x = "date of" + x
    
    # Find y
    yObject = h.head
    y = ""
    if (not yObject.pos_ == "PRON"):
        y = find_compound(parsed, h, yObject, False)  # Find anything that might need to be included in y

    # Find z
    possibleIs = xObject.head
    z = ""
    if (possibleIs.lemma_ == "be"):
        for i in parsed:
            if ((i.pos_ == "NOUN" or i.pos_ == "PROPN") and i.head == possibleIs and not i == xObject):
                zObject = i
                z = find_compound(parsed, h, zObject, False)  # Find anything that might need to be included in z
                break
    return [x, y, z]

def find_standard_xyz_format(parsed, h, propDate):
    # Find x
    xObject = h.head
    x = ""
    if (not xObject.pos_ == "PRON"):
        x = find_compound(parsed, h, xObject, False)  # Find anything that might need to be included in x
        if(propDate):
            x = "date of" + x

    # Find y
    y = ""
    for i in parsed:
        if (i.head == h and not i.pos_ == "PRON"):
            yObject = i
            y = find_compound(parsed, h, yObject, False)  # Find anything that might need to be included in y
            break

    # Find z
    possibleIs = xObject.head
    z = ""
    if (possibleIs.lemma_ == "be"):
        for i in parsed:
            if ((i.pos_ == "NOUN" or i.pos_ == "PROPN") and i.head == possibleIs and not i == xObject):
                zObject = i
                z = find_compound(parsed, h, zObject, False)  # Find anything that might need to be included in z
                break
    return [x, y, z]


def yes_no_questions_get_x_y_z(parse, question):
    xstring, ystring, zstring = "", "", ""

    # Do Z X Y? (Did B. B. King influence Jimi Hendrix?)
    if parse[0].lemma_ == "do":
        xstring, ystring, zstring = find_do_z_x_y(parse)

    # Be Z the X of Y? (Is Donda West the mother of Kanye West)
    elif check_be_z_the_x_of_y(parse) is True:
        xstring, ystring, zstring = find_be_z_the_x_of_y(parse, question)

    # Be Z Y? (Is Shakira a model, Is Michael Jackson alive)
    else:
        xstring, ystring, zstring = find_be_y_z(parse)

    return xstring, ystring, zstring

########################################################################


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
            abort = 1  # If we find, for example, "What x is the y of z", we treat "What x" as if "x" is not there. "What" would be removed under normal circumstances anyway
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


def add_hardcoded_ids(ret, string, typ):
    print(string)
    if (string == "member" and typ == "property"):
        ret.append("P527")  # Has part
    if (string == "real name" and typ == "property"):
        ret.append("P1477")  # Birth name
    if (string == "album" and typ == "property"):
        ret.append("P361") #Part of, add qualifier for "album"

########################################################################

# Count query generation, simply plugs in values for x and y
def gen_count_query(x, x_id, y, y_id, property):
    x = x.replace(" ", "")
    y = y.replace(" ", "")
    y = y.replace(".", "")
    new_query = ((
        """
        SELECT ?%s
        WHERE
        {
          wd:%s p:%s [
          ps:%s wd:%s;
          pq:P1114 ?%s ].
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
        }
        """)
                 % (x, y_id, property, property, x_id, x))
    return new_query


def gen_highest_lowest_query(x, x_id, y, y_id):
    x = x.replace(" ", "")
    y = y.replace(" ", "")
    y = y.replace(".", "")
    new_query = (("""SELECT ?%s ?%s WHERE {wd:%s wdt:%s ?%s"""
                  """. SERVICE wikibase:label { bd:serviceParam"""
                  """ wikibase:language "[AUTO_LANGUAGE],en". } }""")
                 % (x, x+"Label", y_id, x_id, x))
    return new_query


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
            ''' % (y, x, z)
    else:
        query = '''
            SELECT DISTINCT ?answerLabel
                Where{
                %s %s %s .
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en" .
                }
            }
            ''' % (y, x, z)
    return query


########################################################################


# Sends a request to wikidata with a sparql query, returns the result
def run_specific_query(query):
    try:
        data_request = requests.get(url, params={'query': query,
                                                 'format': 'json'})
        data = data_request.json()
        return data['results']['bindings']
    except Exception:
        print("Failed to get data...")
        return None


def find_xyz_answer(x, y, z):
    answer = ""
    depth = 5  # Increase for better chance of finding obscure answers, decrease for slightly better performance and bigger chance to find less obscure answers
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
                        answer = []
                        returned_query = run_specific_query(query)
                        for item in returned_query:
                            for var in item:
                                answer.append(item[var]['value'])
                        if (not answer == []):
                            return answer
    return "No answer was found"


########################################################################

# Can print list answers in a single line
def print_answer(answers):
    for answer in answers:
        print(answer, end='\t', flush=True)
    print('')


########################################################################
def isCase_1(parse):
    if parse[0].lemma_ == 'be' or parse[0].lemma_ == 'do':
        return True
    else:
        return False


def isCase_2(question):
    if "highest" in question or "lowest" in question or "first" in question or "last" in question:
        return True
    return False


def isCase_3(parse):
    if parse[0].text == 'How' and parse[1].text == "many":
        return True
    return False


def isCase_4(parse):
    return False


########################################################################

def findAnswerCase_1(parse, question):
    finalAnswer = []
    candidateAnswer = []
    xstring, ystring, zstring = yes_no_questions_get_x_y_z(parse, question)
    print("x: " + xstring)
    print("y: " + ystring)
    print("z: " + zstring)
    candidateAnswer.append(zstring)
    data = get_results(xstring, ystring)
    if data:
        listAnswers = extract_answer(data)
        if zstring in listAnswers:
            finalAnswer.append('Yes')
        elif candidateAnswer == extract_answer(data):
            finalAnswer.append('Yes')
        else:
            finalAnswer.append('No')
        return finalAnswer
    else:
        # Fail Case
        finalAnswer.append('Could not find answer')
        return finalAnswer


def findAnswerCase_2(parse, times=0):
    if (times >= 8):
        print("Exhausted 8 options, no answer found\n")
        return []
    x, y = highest_lowest_questions_get_x_and_y(parse)
    print("x: " + x + " y: " + y)
    times_tried = permutation[times]
    try:
        x_property = find_property(x, times_tried[0])
        y_element = find_entity(y, times_tried[1])
    except Exception:
        return findAnswerCase_2(parse, times+1)
    sparql_query = gen_highest_lowest_query(x, x_property['id'], y, y_element['id'])
    query_result = run_specific_query(sparql_query)
    if query_result == []:
        return findAnswerCase_2(parse, times+1)
    else:
        answer = []
        for item in query_result:
            for idx, var in enumerate(item):
                if idx == 0:
                    continue
                answer.append(item[var]['value'])
        return answer


def findAnswerCase_3(parse, times=0):
    if (times >= 8):
        print("Exhausted 8 options, no answer found\n")
        return []
    x, y = count_questions_get_x_and_y(parse)
    print("x: " + x + "  y: " + y)
    times_tried = permutation[times]
    try:
        x_property = find_entity(x, times_tried[0])
        y_element = find_entity(y, times_tried[1])
    except Exception:
        return findAnswerCase_3(parse, times+1)
    for i in range(len(count_questions_properties)):
        sparql_query = gen_count_query(x, x_property['id'], y, y_element['id'], count_questions_properties[i])
        query_result = run_specific_query(sparql_query)
        if query_result != []:
            break
    if query_result == []:
        return findAnswerCase_3(parse, times+1)
    else:
        answer = []
        for item in query_result:
            for var in item:
                answer.append(item[var]['value'])
        return answer


def findAnswerCase_4(parse):
    print('Parse 2: Incomplete Code')


def findFailCase(parsed):
    for numh in range(len(parsed)-1, -1, -1):
        h = parsed[numh]
        print (h.lemma_)
        # Find standard case: z is (the) x of y
        if (h.dep_ == "prep" and h.lemma_ == "of"):
            li = find_standard_xyz_format(parsed, h, False)
            x = li[0]
            y = li[1]
            z = li[2]

            print ("the %s of %s is %s" %(x, y, z))
            answer = find_xyz_answer(x, y, z)
            if (not answer == "No answer was found"):
                return answer
        
        # Find questions using the possessive ("'s")
        if (h.tag_ == "POS"):
            print("possessive!")
            li = find_possessive_xyz_format(parsed, h, False)
            x = li[0]
            y = li[1]
            z = li[2]

            print ("the %s of %s is %s" %(x, y, z))
            answer = find_xyz_answer(x, y, z)
            if (not answer == "No answer was found"):
                return answer
        
        # Find questions starting with "when"
        if (h.head.pos_ == "VERB" and h.lemma_ == "when"):
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
    # Find questions starting with "how"
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

    return ["No answer was found"]


########################################################################

def find_answer(question):

    parse = nlp(question)

    for w in parse:
        print("\t \t".join((w.text, w.lemma_, w.pos_, w.tag_, w.dep_,w.head.lemma_)))

    answer = []
    # Yes/No Questions
    if isCase_1(parse) is True:
        answer = findAnswerCase_1(parse, question)

    # Highest/Lowest Questions
    elif isCase_2(question) is True:
        answer = findAnswerCase_2(parse)

    # Count Questions
    elif isCase_3(parse) is True:
        answer = findAnswerCase_3(parse)

    # What/Who/Where/When/How Questions
    elif isCase_4(parse) is True:
        answer = findAnswerCase_4(parse)

    # Fail Case
    else:
        answer = findFailCase(parse)

    print_answer(answer)


def main(argv):
    for sentence in sys.stdin:
        find_answer(sentence)


if __name__ == "__main__":
    main(sys.argv)
