import json

how_the_fuck_should_i_name_this_list = []

files_map = {
    # "filename": [is list, amount of entries (only if is_list == True), default value]
    "backpack.json": [True, 3, [0, 0]], #item, quantity
    "levels.json": [True, 1, [1, 1, 0, 0, 1]], #pickaxe lvl, backpack lvl, prestige, rebirth, stage
    "tokens.json": [True, 2, 0], #prestige, rebirth
    "coins.json": [False, 0, 0],
    "running.json": [False, 0, False],
    "mined.json": [False, 0, 0],
    "bio.json": [False, 0, 0],
    "mult.json": [True, 3, 0] #coins, speed, backpack
}

#load json data
with open("db/helplist.json") as f: helplist = json.load(f)
with open("db/backpack.json") as f: backpack = json.load(f)
with open("db/running.json")  as f: running  = json.load(f)
with open("db/levels.json")   as f: levels   = json.load(f)
with open("db/tokens.json")   as f: tokens   = json.load(f)
with open("db/stages.json")   as f: stages   = json.load(f)
with open("db/blocks.json")   as f: blocks   = json.load(f)
with open("db/emojis.json")   as f: emojis   = json.load(f)
with open("db/coins.json")    as f: coins    = json.load(f)
with open("db/mined.json")    as f: mined    = json.load(f)
with open("db/mult.json")     as f: mult     = json.load(f)
with open("db/bio.json")      as f: bio      = json.load(f)

def sort_by_value(d):
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=True))

def init_entry(d : dict, key : str, is_list : bool, nentries : int = None, default = 0): #sauce (thatOneArchUser#5518 told me to add this, idk why tho)
    if str(key) in d: #if the key is already in the dictionary
        return

    if is_list: #if the value is a list
        if nentries == None:
            nentries = 1 #default number of entries

        if type(default).__name__ == "list": #if default value is a list
            if nentries == 1 or nentries < len(default): #if the number of entries is 1 or the length of default is larger than the amount of entries
                d[str(key)] = default #set value to the list
                return

        d[str(key)] = [default] * nentries #create a list with nentries number of items

    else:
        d[str(key)] = default 

def init_all(key : str):
    for i in files_map.keys(): #for every mapped file
        with open(f"db/{i}") as f: #open it as f
            init_entry(globals()[i[:-5]], key, files_map[i][0], files_map[i][1], files_map[i][2]) #initialize its entries
            save() #save the data

def expand_list(d : dict, key, nentries : int, default = None):
    if len(d[key]) < nentries:
        if default == None:
            default = 0
        for i in range(nentries - len(d[key])):
            d[key].append(default)

def save():
    for i in files_map.keys():
        with open(f"db/{i}", "w+") as f:
            json.dump(globals()[i[:-5]], f)

def clear_db():
    for i in files_map.keys():
        with open(f"db/{i}", "w") as f:
            globals()[i[:-5]].clear()
            save()

def get_subdict_items(d, key):
    l = []
    for i in d.keys():
        l.append(d[i][key])
    
    return l

def get_key_by_subdict_item(d, subkey, item, delm = ","):
    if item in d.keys():
        return item

    for i in d.keys():
        try:
            if d[i][subkey] == item or item in d[i][subkey].split(delm):
                return i
        except:
            continue
    
    return -1
