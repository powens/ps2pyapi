'''
Created on Mar 11, 2013

@author: Torokokill
'''

import urllib.request
import json
import sys
import os
import time
import logging
import hashlib
import pickle

log = logging.getLogger(__name__)

class ChildNotFoundException(Exception):
    '''
    ChildNotFoundException: Thrown whenever TextQuery.getChild() encounters an arg that doesn't childExists
    
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
            yield TextQuery(self.queryUrl, values[i], self.time)
            i = i+1
            
    def __len__(self):
        return len(self.json)     
    
    def isNone(self):
        '''
        Returns True if the JSON object encapsulated is equal to None
        '''
        return self.json == None
    
    def childExists(self, children):
        '''
        Checks to see if the supplied child inside the JSON object exists. Returns True if it does.
        Parameters:
            children: A list of children
        '''
        try:
            self.getChild(children)
            return True
        except ChildNotFoundException:
            return False
 
    def getChild(self, children):
        '''
        Drills down into the JSON object finding a child located at children, throws an ChildNotFoundException if any child in the list doesn't exist
        Returns: 
            If the object is a list or a dictionary, returns a the object wrapped in it's own TextQuery class
            If the object is anything else, return the object itself
        
        Parameters:
            children: A list of children
        '''   
        #Throw the children in a list if there is only one child not in a list
        if type(children) is not list:
            children = [children] 
        currentObj = self.json
        
        #Iterate through the list of children, drilling down into the JSON object
        #Raise an exception if an child is missing
        for child in children:
            if (type(child) is int and type(currentObj) is list and len(currentObj) > child) or child in currentObj:
                currentObj = currentObj[child]
            else:
                raise ChildNotFoundException(str(child) + " not found in " + str(children), self.queryUrl)
        
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

    def __init__(self, serviceId=None, namespace="ps2-beta", log=False, cacheDirectory="./cache"):
        '''
        Constructor. Sets serviceId and namespace.
        
        Parameters:
            serviceId: The service id to use for all queries. Can be set to None to use no service id, as it is not currently required. The starting s: not required
            namespace: The namespace to query from. Defaults to ps2-beta as it is the recommended namespace to use
            logging: Enables or disables logging of queries and any exceptions that are raised from the queries
            cacheDirectory: Directory to use to cache api results. Use None to not use any caching
        '''
        self.setServiceId(serviceId)
        self.namespace = namespace
        self.logging = log
        if log:
            logging.basicConfig(filename="ps2api.log", level=logging.DEBUG)
        self.cacheDirectory = cacheDirectory
        if cacheDirectory:
            if not os.path.exists(cacheDirectory):
                os.makedirs(cacheDirectory)
            
    def buildCollectionList(self):
        '''
        Queries the API for a list of collections, returning that list
        '''
        collectionQuery = self.rawTextApiCall("")
        collections = collectionQuery.getInfo(["datatype_list"])
        collectionList = []
        for collection in collections.json:
            collectionList.append(collection["name"])
        self.collections = collectionList
    
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
    
    def getTextWithRetry(self, collection, action="get", identifier=None, modifier=None, cacheTimeSec=-1, retryTimeSec=5):
        '''
        Performs a text api query. Will continually retry with a configurable retry sleep time until the query succeeds.
        '''
        while True:
            try:
                return self.textApiQuery(collection, action, identifier, modifier, cacheTimeSec)
            except:
                time.sleep(retryTimeSec)
                
    def getImgWithRetry(self, collection, identifier, imageType=None, cacheTimeSec=-1, retryTimeSec=5):
        '''
        Performs an img api query. Will continually retry with a configurable retry sleep time until the query succeeds.
        '''
        while True:
            try:
                return self.rawImgApiQuery(collection, identifier, imageType, cacheTimeSec)
            except:
                time.sleep(retryTimeSec)
    
    def rawImgApiQuery(self, collection, identifier, imageType=None, cacheTimeSec=-1):
        '''
        Sends a raw image call to the API. Returns the Image wrapped in a ImageQuery object if the query succeeds.
        
        Parameters:
            collection: Which collection to get info from
            identifier: Used to refine some queries, for example passing a character id with the character collection
            imageType: Type of image to return
            cacheTimeSec: 
                If greater than 0, check to see if the age of the cache is younger than this. If it is, use the cache instead
                If equal to 0, always use the cached version if it exists
                If less than 0, never use the cache   
        
        '''
        queryUrl = self._constructBaseQueryString() + "/img/" + self.namespace + "/" + self.sanitize(collection) + "/" + self.sanitize(identifier)
        if imageType:
            queryUrl += "/" + imageType
            
        #Check the cache
        cacheFilename = None
        if (self.cacheDirectory is not None) and (cacheTimeSec >= 0):
            #Check to see if the cache file either exists or the cache has expired
            cacheFilename = self.cacheDirectory + "/" + self._getCachefilename(queryUrl)
            try:
                with open(cacheFilename, "rb") as f:
                    #File exists, check it's date and return the cached file
                    st = os.stat(cacheFilename)
                    mtime = st.st_mtime
                    currentTime = time.time()
                    if (currentTime - mtime) < cacheTimeSec:
                        return pickle.load(f)
            except IOError:
                pass
        
        #Perform the query, wrap it inside an ImgQuery object
        timeStart = time.time()
        s = self._makeUrlRequest(queryUrl)
        timeEnd = time.time()
        query = ImgQuery(queryUrl, s, timeEnd - timeStart)
        
        #If caching is enabled and we have a cache time, cache the query
        if cacheFilename is not None:
            with open(cacheFilename, "wb+") as f:
                pickle.dump(query, f)
        return query
        
        return query
        
    def textApiQuery(self, collection, action="get", identifier=None, modifiers=None, cacheTimeSec=-1):
        '''
        Sends makes a request for json data to the API. Returns the JSON object wrapped in a TextQuery object if the query succeeds.
        Raw queries use a raw string of modifiers rather than a nice list
        
        Parameters:
            collection: Which collection to get info from
            action: Use "get" to get information, "count" to return the number of records
            identifier: Used to refine some queries, for example passing a character id with the character collection
            modifiers: All the query modifiers. Can either be a raw string of modifiers, or a list
            cacheTimeSec: 
                If greater than 0, check to see if the age of the cache is younger than this. If it is, use the cache instead
                If equal to 0, always use the cached version if it exists
                If less than 0, never use the cache        
        '''
        #Construct the query string URL
        queryUrl = self._constructBaseQueryString() + "/" + self.sanitize(action) + "/" + self.namespace + "/" + self.sanitize(collection)
        if identifier:
            queryUrl += "/" + self.sanitize(identifier)
        if modifiers:
            if type(modifiers) is list:
                queryUrl += "?" + self._buildModifierString(modifiers)
            else:
                queryUrl += "?" + self.sanitize(modifiers) 
              
        #Check the cache
        cacheFilename = None
        if (self.cacheDirectory is not None) and (cacheTimeSec >= 0):
            #Check to see if the cache file either exists or the cache has expired
            cacheFilename = self.cacheDirectory + "/" + self._getCachefilename(queryUrl)
            try:
                with open(cacheFilename, "rb") as f:
                    #File exists, check it's date and return the cached file
                    st = os.stat(cacheFilename)
                    mtime = st.st_mtime
                    currentTime = time.time()
                    if (currentTime - mtime) < cacheTimeSec:
                        return pickle.load(f)
            except IOError:
                pass
        #elif (self.cacheDirectory is None) or (cacheTimeSec < 0):
        
        #Request make the URL request and wrap the returned JSON object inside a TextQuery class
        timeStart = time.time()
        s = self._makeUrlRequest(queryUrl)
        timeEnd = time.time()
        query = TextQuery(queryUrl, json.loads(s.decode("utf-8")), timeEnd - timeStart)
        
        #If caching is enabled and we have a cache time, cache the query
        if cacheFilename is not None:
            with open(cacheFilename, "wb+") as f:
                pickle.dump(query, f)
        return query
            
    def _makeUrlRequest(self, queryString):
        '''
        Sends a request off to the API. Logs and rethrows a ton of exceptions
        
        Parameters:
            queryString -- URL to query
        '''
        log.debug("Sending request: %s", queryString)
        try:
            with urllib.request.urlopen(queryString) as url:
                s = url.read()
                if s == None:
                    #This should never happen
                    log.debug("s is None")
                    raise Exception("s is None")
                return s
        except urllib.error.HTTPError as err:
            log.debug("API HTTPError: " + str(err.code) + " " + err.msg)
            raise
        except urllib.error.URLError as err:
            log.debug("API URLError " + str(err))
            raise
        except:
            e = sys.exc_info()[0]
            logging.debug("API GenericError: " + str(e))
            raise
    
        
    def _constructBaseQueryString(self):
        '''
        Returns the base query string of http://census.soe.com/s:serviceId
        '''
        queryString = "http://census.soe.com"
        if self.serviceId:
            queryString += "/s:" + self.sanitize(self.serviceId)
            
        return queryString
    
    def _getCachefilename(self, filename):
        '''
        Takes a filename(without a directory) and returns an md5 hash of it
        
        Paramters:
            filename -- Name of the file to hash
        '''
        return hashlib.md5(filename.encode()).hexdigest()
    
    def _buildModifierString(self, modifierList):
        '''
        Builds a modifier query string from a list. 
        For example: 
            Turns {"start":["10"], "resolve":["tuhtles(name,nope),stuff"],"name.lower":["torokokill"]}
            Into c:start=10&c:resolve=tuhtles(name,nope),stuff&name.lower=torokokill
            
        Parameters:
            modifierList -- List of modifiers to turn into a string
        '''
        modifierStr = ""
        for k,v in modifierList.items():
            k = self.sanitize(k)
            v = self.sanitize(v)
            if k in PS2Api.validQueryArgs:
                modifierStr += "&c:" + k + "="
            else:
                modifierStr += "&" + k + "="
                
            modifierStr += ','.join(v)
        return modifierStr[1:]
                    


            
