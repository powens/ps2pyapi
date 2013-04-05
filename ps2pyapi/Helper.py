'''
Created on Mar 20, 2013

@author: Torokokill
'''
import pickle

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
    def getWeaponNameById(weaponid, api):
        return Helper._getCache(api, "weaponNameCache", weaponid, "item", "c:show=name.en", ["item_list", 0, "name", "en"])
        
    @staticmethod
    def getVehicleNameById(vehicleid, api):
        return Helper._getCache(api, "vehicleNameCache", vehicleid, "vehicle", "c:show=name.en", ["vehicle_list", 0, "name", "en"])
    
