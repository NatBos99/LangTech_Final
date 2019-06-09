#!/usr/bin/python3
import sys
import requests
import re
import spacy

nlp = spacy.load('en_core_web_md')

url = 'https://query.wikidata.org/sparql'
api_url = 'https://www.wikidata.org/w/api.php'
