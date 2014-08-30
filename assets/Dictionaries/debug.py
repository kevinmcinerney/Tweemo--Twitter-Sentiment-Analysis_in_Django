with open("/home/kevin/django-kevin/bin/twitter/assets/Dictionaries/output.txt") as f:
		for line in f:
			print line
	       		(key, val) = line.split('\t')
	       		scores[key] = int(val)
