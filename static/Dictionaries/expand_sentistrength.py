from nltk.corpus import stopwords,names
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import brown
import sys
from nltk import WordPunctTokenizer

brown_words_1 = brown.words(categories='news')
brown_words_2 = brown.words(categories='humor')
brown_words_3 = brown.words(categories='science_fiction')
brown_words_4 = brown.words(categories='government')
brown_words_5 = brown.words(categories='lore')
brown_words_6 = brown.words(categories='learned')
brown_words_7 = brown.words(categories='fiction')
brown_words_8 = brown.words(categories='hobbies')
brown_words_9 = brown.words(categories='editorial')
brown_words_10 = brown.words(categories='adventure')
brown_words_11 = brown.words(categories='belles_lettres')
brown_words_12 = brown.words(categories='romance')
brown_words_13 = brown.words(categories='reviews')
brown_words_14 = brown.words(categories='mystery')

brown_total = brown_words_1 + brown_words_2 + brown_words_3 + brown_words_4 + brown_words_5 + brown_words_6 + brown_words_7 + brown_words_8 + brown_words_9 + brown_words_10 + brown_words_11 + brown_words_12 + brown_words_13 + brown_words_14

st = LancasterStemmer()
stopw = set(stopwords.words('english'))
word_splitter = WordPunctTokenizer()

afinn = open(sys.argv[1])
clean_senti = open(sys.argv[2])


afinn_dic= {}
afinn_words = []
for line in afinn:
	term, score  = line.split("\t")  # The file is tab-delimited. "\t" means "tab character"
	afinn_dic[term] = score


senti_dic = {}
for line in clean_senti:
	term, score  = line.split("\t")  # The file is tab-delimited. "\t" means "tab character"
	senti_dic[term] = score

senti2 = {}
senti2 = senti_dic.copy()
	
set_brown_words = ()
brown_words_list = []
for word in brown_total:
	word = word.lower()
	brown_words_list.append(word)
set_brown_words = set(brown_words_list)


for word in senti2:
	for word2 in set_brown_words:
		if word[0:2] == word2[0:2] and word in word2 and word2 not in stopw:
			senti_dic[str(word2)] = str(senti_dic[word])

for word in afinn_dic:
	if word not in senti_dic:
		senti_dic[str(word)] = str(afinn_dic[word])

for i in senti_dic:
	print str(i) + str('\t') + str(senti_dic[i]).rstrip('\n')


