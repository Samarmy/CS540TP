import sys
import os
from nltk.parse import stanford
dir_path = '<put your directory path here>'

os.environ['STANFORD_PARSER'] = dir_path + '/stanford-parser-full-2018-10-17'
os.environ['STANFORD_MODELS'] = dir_path + '/stanford-parser-full-2018-10-17'

parser = stanford.StanfordParser(model_path= dir_path + '/englishPCFG.ser.gz')
input = ["Hello my name is Sam."]

if(len(sys.argv) > 1): input = []
for x in sys.argv[1:]: input.append(x)

sentences = parser.raw_parse_sents(input)
for y in input: print(y)

for line in sentences:
    for sentence in line:
        print(sentence)
#         sentence.draw() #GUI
