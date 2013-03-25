'''
Created on Mar 11, 2013

@author: Torokokill
'''

import urllib.request
import json
import sys
import time
import logging

log = logging.getLogger(__name__)

class ArgNotFoundException(Exception):
    '''
    ArgNotFoundException: Thrown whenever TextQuery.get() encounters an arg that doesn't exists
    
    Parameters:
        msg: A small message stating which arg in the list is invalid
        query: The query url
    '''
    def __init__(self, msg, query):
        self.msg = msg
        self.query = query
        
    def __str__(self):
        return repr(self.msg + " (" + self.query + ")")

class ImgQuery(object):
    '''
    Encapsulates an Image object return from the API.
    
    Parameters:
        data: The raw image data to encapsulate
    '''
    def __init__(self, queryUrl, data, time):
        self.data = data
        self.queryUrl = queryUrl
        self.time = time
        
    def saveToDisk(self, filename):
        '''
        Write the image to disk with the given filename
        
        Parameters:
            filename: The filename to save 
        '''
        with open(filename, "wb+") as f:
            f.write(self.data)

class TextQuery(object):
    '''
    Encapsulates a JSON object returned from the API.
    
    Parameters
        json: The JSON object to encapsulate
    '''
    def __init__(self, queryUrl, json, time):
        self.json = json
        self.queryUrl = queryUrl
        self.time = time
    
    def __iter__(self):
        '''
        Iterator. Iterates through the the list of objects that are directly connected to the object
        ''' 
        #Put all possible objects into an array
        values = []
        if type(self.json) is dict:
            values = list(self.json.items())
        elif type(self.json) is list:
            values = self.json
        else:
            values = [self.json]
            
        i = 0
        valuesLen = len(values)
        while i < valuesLen:
            yield TextQuery(self.queryUrl, values[i])
            i = i+1    
    
    def isNone(self):
        '''
        Returns True if the JSON object encapsulated is equal to None
        '''
        return self.json == None
    
    def exists(self, args):
        '''
        Checks to see if the supplied child inside the JSON object exists. Returns True if it does.
        Parameters:
            args: A list of args
        '''
        try:
            self.get(args)
            return True
        except ArgNotFoundException:
            return False
 
    def get(self, args):
        '''
        Drills down into the JSON object finding a child located at args, throws an ArgNotFoundException if any arg in the list doesn't exist
        Returns: 
            If the object is a list or a dictionary, returns a the object wrapped in it's own TextQuery class
            If the object is anything else, return the object itself
        
        Parameters:
            args: A list of args
        '''   
        #Throw the args in a list if there is only one arg not in a list
        if type(args) is not list:
            args = [args] 
        currentObj = self.json
        
        #Iterate through the list of args, drilling down into the JSON object
        #Raise an exception if an arg is missing
        for arg in args:
            if (type(arg) is int and type(currentObj) is list and len(currentObj) > arg) or arg in currentObj:
                currentObj = currentObj[arg]
            else:
                raise ArgNotFoundException(str(arg) + " not found in " + str(args), self.queryUrl)
        
        #If the object at the end of the chain is a dict or a list, wrap the object in a TextQuery object. Return it. 
        if type(currentObj) is dict or type(currentObj) is list:
            return TextQuery(self.queryUrl, currentObj, self.time)
        else:    
            return currentObj
        

class PS2Api(object):
    '''
    The API wrapper. Queries the API for info and returns the results wrapped in TextQuery and ImgQuery objects
    '''
    validQueryArgs = ["start","limit","show","hide","sort","has","resolve","case"]
    validModifiers = ["!", "[", "<", "]", ">", "^", "*"]

    def __init__(self, serviceId=None, namespace="ps2-beta", log=False):
        '''
        Constructor. Sets serviceId and namespace.
        
        Parameters:
            serviceId: The service id to use for all queries. Can be set to None to use no service id, as it is not currently required. The starting s: not required
            namespace: The namespace to query from. Defaults to ps2-beta as it is the recommended namespace to use
            logging: Enables or disables logging of queries and any exceptions that are raised from the queries
        '''
        self.setServiceId(serviceId)
        self.namespace = namespace
        self.logging = log
        if log:
            logging.basicConfig(filename="ps2api.log", level=logging.DEBUG)
    
    def setServiceId(self, serviceId):
        '''
        Sets the service id. Does a bit of checking to make sure the service id has proper formatting.
        
        Parameters:
            serviceId: What to set the service id to. The starting s: not required
        '''
        if serviceId is not None:
            serviceId = serviceId.replace(" ", "%20").replace("/", "").replace("s:", "")
        self.serviceId = serviceId
        
    def sanitize(self, s):
        '''
        Sanitizes the query url
        
        Parameters:
            s: String to sanitize
        '''
        for ch in ['?','+','/',';','$','@']:
            if ch in s:
                s = s.replace(ch, '')
        
        s = s.replace(" ", "%20")
        return s
    
    def getTextWithRetry(self, collection, action="get", identifier=None, args=None, retryTimeSec=5):
        '''
        Performs a text api query. Will continually retry with a configurable retry sleep time until the query succeeds.
        '''
        while True:
            try:
                return self.rawTextApiQuery(collection, action, identifier, args)
            except:
                time.sleep(retryTimeSec)
                
    def getImgWithRetry(self, collection, identifier, imageType=None, retryTimeSec=5):
        '''
        Performs an img api query. Will continually retry with a configurable retry sleep time until the query succeeds.
        '''
        while True:
            try:
                return self.rawImgApiQuery(collection, identifier, imageType)
            except:
                time.sleep(retryTimeSec)
    
    def textApiQuery(self, collection, action="get", identifier=None, args=None):
        pass
    
    def imgApiQuery(self, collection, identifier, imageType=None):
        pass
    
    def rawImgApiQuery(self, collection, identifier, imageType=None):
        '''
        Sends a raw image call to the API. Returns the Image wrapped in a ImageQuery object if the query succeeds.
        
        Parameters:
            collection -- Which collection to get info from
            identifier -- Used to refine some queries, for example passing a character id with the character collection
            imageType -- Type of image to return
        
        '''
        queryUrl = self._constructBaseQueryString() + "/img/" + self.namespace + "/" + self.sanitize(collection) + "/" + self.sanitize(identifier)
        if imageType:
            queryUrl += "/" + imageType
        
        timeStart = time.time()
        s = self._makeUrlRequest(queryUrl)
        timeEnd = time.time()
        return ImgQuery(queryUrl, s, timeEnd - timeStart)
        
    def rawTextApiQuery(self, collection, action="get", identifier=None, args=None):
        '''
        Sends a raw json call to the API. Returns the JSON object wrapped in a TextQuery object if the query succeeds. 
        
        Parameters:
            collection -- Which collection to get info from
            action -- use "get" to get information, "count" to return the number of records
            identifier -- used to refine some queries, for example passing a character id with the character collection
            args -- all the query modifiers, joined by &
        '''
        #Construct the query string URL
        queryUrl = self._constructBaseQueryString() + "/" + self.sanitize(action) + "/" + self.namespace + "/" + self.sanitize(collection)
        if identifier:
            queryUrl += "/" + self.sanitize(identifier)
        if args:
            queryUrl += "?" + self.sanitize(args) 
        
        #Request make the URL request and wrap the returned JSON object inside a TextQuery class
        timeStart = time.time()
        s = self._makeUrlRequest(queryUrl)
        timeEnd = time.time()
        return TextQuery(queryUrl, json.loads(s.decode("utf-8")), timeEnd - timeStart)
    
    def _makeUrlRequest(self, queryString):
        '''
        Sends a request off to the API. Rethrows a ton of exceptions
        
        Parameters:
            queryString: URL to query
        '''
        log.debug("API: %s", queryString)
        try:
            with urllib.request.urlopen(queryString) as url:
                s = url.read()
                if s == None:
                    log.debug("s is None")
                    raise Exception("s is None")
                return s
        except urllib.error.HTTPError as err:
            log.debug("API HTTP ERROR: " + str(err.code) + " " + err.msg)
            raise
        except urllib.error.URLError as err:
            log.debug("URLError " + str(err))
            raise
        except:
            e = sys.exc_info()[0]
            logging.debug("GenericError: " + str(e))
            raise
    
        
    def _constructBaseQueryString(self):
        '''
        Returns the base query string of http://census.soe.com/s:serviceId
        '''
        queryString = "http://census.soe.com"
        if self.serviceId:
            queryString += "/s:" + self.sanitize(self.serviceId)
            
        return queryString
    
    def buildArgsString(self, args):
        argStr = ""
        for k,v in args.items():
            if k in PS2Api.validQueryArgs:
                argStr += "&c:" + k + "="
            else:
                argStr += "&" + k + "="
                
            argStr += ','.join(v)
        return argStr[1:]
                    


            
