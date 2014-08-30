import sys
import json
from nltk.stem.lancaster import LancasterStemmer
 

st = LancasterStemmer()
sentilist = open(sys.argv[1])
afinn = open(sys.argv[2])
scores = {} # initialize an empty dictionary
score = 0
term = ""
count = 0
for line in sentilist:
	for i in line.split('\t'):
		count += 1
		if count == 1:
			term = i
		elif count == 2:
			score = i
		else:
			continue
	scores[term] = int(score)
	count = 0
s = ''
dic = {}
for i in scores:
	for letter in i:
		if letter != '*':
			s += letter
	dic[st.stem(s)] = scores[i]
	s = ''
	
#for i in dic:
	#print i + str(" ") + str(dic[i])

ascores = {}
for line in afinn:
	term2, score2  = line.split("\t")  # The file is tab-delimited. "\t" means "tab character"
	ascores[st.stem(term2)] = int(score2)  

#for i in ascores:
	#print i + str(" ") + str(ascores[i])	

for i in ascores:
	if i not in dic:
		dic[i] = ascores[i]

for i in dic:
	print i + str("\t") + str(dic[i])	




