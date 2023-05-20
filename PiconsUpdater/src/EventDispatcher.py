handler = []


def hasEventListener(eventType, function):
	for e in handler:
		if e[0] == eventType and e[1] == function:
			return True
	return False


def addEventListener(eventType, function):
	if hasEventListener(eventType, function) == False:
		handler.append([eventType, function])


def removeEventListener(eventType, function):
	for e in handler:
		if e[0] == eventType and e[1] == function:
			handler.remove(e)


def dispatchEvent(eventType, *arg):
	for e in handler:
		if e[0] == eventType:
			if arg is not None and len(arg) > 0:
				e[1](*arg)
			else:
				e[1]()
