ps2pyapi
========

torokokill -- torokokill@gmail.com

Python API wrapper for the Planetside 2 stats API

Installation
------------

ps2pyapi was requires Python version 3.3.

To use, just copy the ps2pyapi directory wherever you like.

Getting Started
---------------

import ps2pyapi and create a wrapper object by creating an instance of PS2Api. To perform a text based query, PS2Api::rawTextApiQuery(). Use PS2Api::rawImgApiQuery() to query for images. The returned queries are wrapped inside of TextQuery and ImgQuery objects respectively. TextQuery objects are iterable, and will iterate on the top level container. To obtain child objects, TextQuery::exists() will check if such a child exists and TextQuery::get() will get the child object, wrapped inside it's own TextQuery object.

ps2pyapi.Helper contains a (currently) small set of helper functions, including caching weapon and vehicle id to name resolutions.

Here is a small example:
```python
		import ps2pyapi
		api = ps2pyapi.PS2Api()
		
		query = api.rawTextApiQuery("character", "get", None, "name.first_lower=torokokill&c:show=name.first,type.faction,id&c:resolve=online_status,outfit")
        
		if query.exists(["character_list", 0]):
            character = query.get(["character_list", 0])
            name = character.get(["name", "first"])
            outfit = None
            try:
                outfit = character.get(["outfit", "alias"])
            except ps2pyapi.ArgNotFoundException:
                pass
            faction = character.get(["type", "faction"])
            isOnline = character.get(["online_status"])
            charId = character.get(["id"])
            
			print("[" + outfit + "]" + name + " fights for " + faction.upper() + " and is " + ("online" if isOnline != "0" else "offline"))
```

Version History
---------------

0.0.1:
*	Initial version on Github