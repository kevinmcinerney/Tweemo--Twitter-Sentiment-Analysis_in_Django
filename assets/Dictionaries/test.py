import sys

sup = open(sys.argv[1])

sup_dic= {}
for line in sup:
	term, score  = line.split('\t')  # The file is tab-delimited. "\t" means "tab character"
	print line
	sup_dic[term] = score

