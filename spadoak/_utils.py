
# From the Python 3 documentation
# https://docs.python.org/3/tutorial/errors.html#exceptions
class InputError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """


class ValueRetrieveError(Exception):
    """Exception raised when attempting a value or object
       that could not be retrieved.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

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
