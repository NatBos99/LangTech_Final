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
    return ('no results')


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


# Can print list answers in a single line
def print_answer(answers):
    for answer in answers:
        print(answer, end='\t', flush=True)
    print('')


########################################################################
def isCase_1(parse):
    if parse[0].text == 'Is':
        return True
    elif parse[0].text == 'Are':
        return True
    elif parse[0].text == 'Was':
        return True
    elif parse[0].text == 'Were':
        return True
    elif parse[0].text == 'Does':
        return True
    elif parse[0].text == 'Did':
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

def findAnswerCase_1(parse):
    finalAnswer = []
    questionAnswer = []

    # Test Case: Is Donda West the mother of Kanye West
    questionAnswer.append('Donda West')
    xstring = 'mother'
    ystring = 'Kanye West'

    data = get_results(xstring, ystring)
    # fail Case
    if data == 'no results':
        finalAnswer.append('Could not find answer')
    else:
        if questionAnswer == extract_answer(data):
            finalAnswer.append('Yes')
        else:
            finalAnswer.append('No')
    return finalAnswer


def findAnswerCase_2(parse, times=0):
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
        return None
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

########################################################################


def find_answer(question):

    parse = nlp(question)

    for w in parse:
        print("\t \t".join((w.text, w.lemma_, w.pos_, w.tag_, w.dep_,w.head.lemma_)))

    answer = []
    # Yes/No Questions
    if isCase_1(parse) is True:
        answer = findAnswerCase_1(parse)

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
        answer.append('Could not find answer')

    print_answer(answer)


def main(argv):
    for sentence in sys.stdin:
        find_answer(sentence)


if __name__ == "__main__":
    main(sys.argv)
