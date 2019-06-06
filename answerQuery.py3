#!/usr/bin/python3

import sys
import requests
import re
import spacy


def print_example_queries():
    print ('''    What is the national anthem of Germany?
    The birth name of Snoop Dogg is?
    tell me who the composer of bohemian rhapsody is
    What was the nickname of Michael Jackson
    Who are the composers of "Happy Birthday"?
    Patty Hill is the composer of what song?
    Who were the siblings of Michael Jackson?
    What is the occupation of Stef Bos?
    The composer of Für Elise was:
    Beethoven is what of Fur Elise?
    ''')
    # This script does not yet take the part after "What" into account for "... is the ... of what ...?" questions


def find_compound(parced, h, x):
    # Find any words that should be part of x but are not automatically found
    compound = ""
    abort = 0
    for i in parced:
        if i == x:
            if (abort == 0):
                return compound + x.lemma_
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


def find_x_of_y_is_z(parced):
    for numh in range(len(parced)-1, 0, -1):
        h = parced[numh]
        if (h.dep_ == "prep" and h.lemma_ == "of"):

            # Find x
            xObject = h.head
            x = ""
            if (not xObject.pos_ == "PRON"):
                x = find_compound(parced, h, xObject)  # Find anything that might need to be included in x

            # Find y
            y = ""
            for i in parced:
                if (i.head == h and not i.pos_ == "PRON"):
                    yObject = i
                    y = find_compound(parced, h, yObject)  # Find anything that might need to be included in y
                    break

            #  Find z
            possibleIs = xObject.head
            z = ""
            if (possibleIs.lemma_ == "be"):
                for i in parced:
                    if ((i.pos_ == "NOUN" or i.pos_ == "PROPN") and i.head == possibleIs and not i == xObject):
                        zObject = i
                        z = find_compound(parced, h, zObject)  # Find anything that might need to be included in z
                        break

            print ("the %s of %s is %s" % (x, y, z))
            answer = ""
            depth = 5
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


def add_hardcoded_answers(ret, string, typ):
    print(string)
    if (string == "member" and typ == "property"):
        ret.append("P527")  # Has part
    if (string == "real name" and typ == "property"):
        ret.append("P1477")  # Birth name


def get_id(string, idType):
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action': 'wbsearchentities',
              'language': 'en',
              'format': 'json'
             }
    if idType == 'property':
        params['type'] = 'property'

    params['search'] = string.rstrip()
    json = requests.get(url, params).json()
    ret = []
    add_hardcoded_answers(ret, string, idType)
    try:
        for i in json['search']:
            print("{}\t{}\t{}".format(i['id'], i['label'], i['description']))
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


def find_answer_to_query(query):
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    answer = ""
    for item in data['results']['bindings']:
        for var in item:
            # print(item[var]['value'])
            answer += item[var]['value']
            answer += "\n"
    answer = answer.strip("\n")
    return answer


def create_and_fire_query(line):
    nlp = spacy.load('en_core_web_md')
    parsed = nlp(line)
    # for h in parced:
        # print("\t".join((h.text, h.lemma_, h.pos_,h.tag_, h.dep_, h.head.lemma_)))
    # Look for "... is ... of ..." questions
    return find_x_of_y_is_z(parsed)


# the main function was copied from the slides
def main(argv):
    print_example_queries()
    for line in sys.stdin:
        line = line.rstrip()  # removes newline
        answer = create_and_fire_query(line)
        print(answer)


if __name__ == "__main__":
    main(sys.argv)
