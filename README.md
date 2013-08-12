ps2pyapi
========

torokokill -- torokokill@gmail.com

Python API wrapper for the Planetside 2 stats API

Installation
------------

ps2pyapi requires Python version 3.3.

To use, just copy the ps2pyapi directory wherever you like.

Getting Started
---------------

Begin with **import ps2pyapi**. Create a wrapper object by creating an instance of **PS2Api**. To perform a text based query, **PS2Api::textApiQuery()**. Use **PS2Api::imgApiQuery()** to query for images. The returned queries are wrapped inside of TextQuery and ImgQuery objects respectively. TextQuery objects are iterable, and will iterate on the top level container. To obtain child objects, TextQuery::childExists() will check if such a child exists and TextQuery::getChild() will get the child object, wrapped inside it's own TextQuery object.

ps2pyapi.Helper contains a (currently) small set of helper functions, including having a cache of weapon and vehicle id to name resolutions.

Here is a small example:
```python
import ps2pyapi
api = ps2pyapi.PS2Api()
		
query = api.textApiQuery("character", "get", None, "name.first_lower=torokokill&c:show=name.first,type.faction,id&c:resolve=online_status,outfit")
        
if query.childExists(["character_list", 0]):
    character = query.getChild(["character_list", 0])
    name = character.getChild(["name", "first"])
    outfit = ""
    try:
        outfit = "[" + character.getChild(["outfit", "alias"]) + "]"
    except ps2pyapi.ChildNotFoundException:
        pass
    faction = character.getChild(["type", "faction"])
    isOnline = character.getChild(["online_status"])
            
    print(outfit + name + " fights for " + faction.upper() + " and is " + ("online" if isOnline != "0" else "offline"))
```

TODO
----
- [x] Caching
- [ ] A nicer way to deal with modifier strings

Version History
---------------
0.0.4:
*   Added TextQuery.getChildIfExists() lazy method: Returns the child if it exists, None if it does not.
*   Added TextQuery.findChildWithField() method: Searches all immediate child objects for a child object with a fieldName equal to fieldValue. If it finds one, it returns that immediate child object, wrapped in a TextQuery object.
*   Added a language parameter to Helper.getWeaponNameById() and Helper.getVehicleNameById(), defaults to English
*   Added Helper.cacheTextQueryToFile(), Helper.loadTextQueryFromFile() and Helper.printTextQuery() methods
*   Fixed a bug when performing a query with modifiers in an array.

0.0.3:
*   Updated the default namespace to ps2:v1
*   Added some better query error handling inside of TextQuery.

0.0.2:
*	Added caching, lots of refactoring done to unify terminology and make it easier to understand the code.

0.0.1:
*	Initial version on Github
