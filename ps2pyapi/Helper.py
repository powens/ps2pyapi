'''
Created on Mar 20, 2013

Version 0.0.4

@author: Torokokill
'''
import pickle
import json

class Helper(object):
    @staticmethod
    def _getCache(api, cacheFileName, lookupId, lookupFailCollection, lookupFailModifier, lookupFailInfoLocation):
        if int(lookupId) <= 0:
            return None
        
        cache = {}
        try:
            with open(cacheFileName, "rb") as f:
                cache = pickle.load(f)
        except IOError:
            with open(cacheFileName, "wb+") as f: 
                pickle.dump(cache, f)
            
        if lookupId not in cache:
            query = api.textApiQuery(lookupFailCollection, "get", lookupId, lookupFailModifier)
            if len(query.getChild([lookupFailInfoLocation[0]]).json) == 0: 
                return "Unknown"
            cache[lookupId] = query.getChild(lookupFailInfoLocation)
            with open(cacheFileName, "wb+") as f:
                pickle.dump(cache, f)
        
        return cache[lookupId] 
    
    @staticmethod
    def getWeaponNameById(weaponid, api, language="en"):
        return Helper._getCache(api, "weaponNameCache", weaponid, "item", "c:show=name." + language, ["item_list", 0, "name", language])
        
    @staticmethod
    def getVehicleNameById(vehicleid, api, language="en"):
        return Helper._getCache(api, "vehicleNameCache", vehicleid, "vehicle", "c:show=name." + language, ["vehicle_list", 0, "name", language])
    
    @staticmethod
    def cacheTextQueryToFile(filename, textQuery):
        with open(filename, "wb+") as f:
            pickle.dump(textQuery, f)
    
    @staticmethod
    def loadTextQueryFromFile(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
        
    @staticmethod
    def printTextQuery(textQuery):
        print(json.dumps(textQuery.json, sort_keys=True, indent=4, separators=(',', ': ')))