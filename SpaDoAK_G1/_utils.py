def fetchIfNotDef(maybedefined,dictionary,key,default=None,conversion=(lambda x:x)):
	if maybedefined != None:
		result = maybedefined
	else:
		if key in dictionary:
			result = conversion(dictionary[key])
		else:
			result = default
	return result	

def fetchOrDefault(dictionary,key,default=None,conversion=(lambda x:x)):
	if key in dictionary:
		result = conversion(dictionary[key])
	else:
		result = default
	return result
