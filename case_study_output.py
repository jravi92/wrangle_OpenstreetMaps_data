import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re
import codecs
import json



        
#Opening the OSM file 
osm_file=open("bengaluru_india.osm")


## For printing sample of file content to get idea about the file content
x=open("bengaluru_india.osm")
#print x.read(1000000)


#part 1 -----------------
#for counting the number of tags present
count=0
id_=[]
#------------------------

#part 2 ++++++++++++++++++++
# to read and analyse the key and value from osm file
k=[]
v=[]
#+++++++++++++++++++++++++++

#part 3 =========================================================
# auditing the  street names from the osm file and correcting thr anomalies
street_type_re=re.compile(r'\b\S+\.?$', re.IGNORECASE)

lower = re.compile(r'^([a-z]|_)*$')
upper = re.compile(r'^([A-Z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')



street_types= defaultdict(set)

expected = ["Street", "Avenue", "Cross", "Main", "Layout", "Nagar", "Park", "Road"]

mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Road": "Road",
            "road": "Road",
            "cross": "Cross",
            "ROad": "Road",
            "ROAD": "Road"}

counts = defaultdict(int)
keys = {"lower": 0, "upper":0 , "lower_colon": 0, "problemchars": 0, "other": 0}


def update_name(name, mapping):
    after = []
    # Split name string to test each part of the name;
    # Replacements may come anywhere in the name.
    for part in name.split(" "):
        # Check each part of the name against the keys in the correction dict
        if part in mapping.keys():
            # If exists in dict, overwrite that part of the name with the dict value for it.
            part = mapping[part]
        # Assemble each corrected piece of the name back together.
        after.append(part)
    # Return all pieces of the name as a string joined by a space.
    return " ".join(after)



def audit_street_type(street_types, street_name):
    m=street_type_re.search(street_name)
    if m:
        street_type =m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            

def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key= lambda s:s.lower())
    for k in keys:
        v=d[k]
        print "%s: %d" % (k,v)
    
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

postcode_re = re.compile(r'^\d{6}$')

def is_postal(elem):
    return (elem.attrib['k'] == "addr:postcode")

def update_postal_code(name):
    new_post=name.replace(" ", "")
    po=postcode_re.search(new_post)
    if po:
        return new_post
    elif(len(new_post)==7):
        new_post=name.replace("000", "00")
        return new_post
    else:
        return "NA", name


def key_type(element, keys):
    if element.tag == "tag":
        # YOUR CODE HERE
        k_value=element.attrib["k"]
        if lower.search(k_value) is not None:
            keys['lower'] += 1
        elif lower_colon.search(k_value) is not None:
            keys['lower_colon'] += 1
        elif problemchars.search(k_value) is not None:
            keys["problemchars"] += 1
            print k_value
        elif upper.search(k_value) is not None:
            keys["upper"] += 1    
        else:
            keys['other'] += 1
        
    return keys
#===============================================================


#part 4
####################################################
# formatting the data in JSON format and writing in the output file
file_out = "{0}.json".format("bengaluru_india.osm")
data = []
#problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
count2=0
pretty = False

unique_user = defaultdict(int)

def is_address(elem):
    if elem.attrib['k'][:5] == "addr:":
        return True

def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way":
        address_info = {}
        nd_info = []
        #pprint.pprint(element.attrib)
        node["type"] = element.tag
        node["id"] = element.attrib["id"]
        if "visible" in element.attrib.keys():
            node["visible"] = element.attrib["visible"]
        if "lat" in element.attrib.keys():
            node["pos"] = [float(element.attrib['lat']), float(element.attrib['lon'])]
        node["created"] = {"version": element.attrib['version'],
                            "changeset": element.attrib['changeset'],
                            "timestamp": element.attrib['timestamp'],
                            "uid": element.attrib['uid'],
                            "user": element.attrib['user']}
        uid=node["created"]["uid"]
        unique_user[uid] += 1
        for tag in element.iter("tag"):
            #print tag.attrib
            p = problemchars.search(tag.attrib['k'])
            if p:
                #print "PROBLEM:", p.group()
                continue
            elif is_address(tag):
                if ":" in tag.attrib['k'][5:]:
                    #print "Bad Address:", tag.attrib['k'], "--", tag.attrib['v']
                    continue
                else:
                    #address_info[tag.attrib['k'][5:]] = tag.attrib['v']
                    if is_street_name(tag):
                        #audit_street_type(street_types, tag.attrib['v'])
                        street_name=tag.attrib['v']
                        better_name=update_name(street_name, mapping)
                        address_info['Street'] = better_name
                    if is_postal(tag):
                        postal_code=tag.attrib['v']
                        checked_post=update_postal_code(postal_code)
                        address_info['Postcode'] = checked_post
                        #print checked_post
                    else:
                        address_info[tag.attrib['k'][5:]] = tag.attrib['v']
                    #print "Good Address:", tag.attrib['k'], "--", tag.attrib['v']
            else:
                node[tag.attrib['k']] = tag.attrib['v']
                #print "Outside:", tag.attrib['k'], "--", tag.attrib['v']
        if address_info != {}:
            node['address'] = address_info
        for tag2 in element.iter("nd"):
            nd_info.append(tag2.attrib['ref'])
            #print tag2.attrib['ref']
        if nd_info != []:
            node['node_refs'] = nd_info
        return node
    else:
        return None
#####################################################################################33
    
#Main program

cuisine= defaultdict(int)
religion= defaultdict(int)
    
# for accessing inner content of file
with codecs.open(file_out, "w") as fo:
    for event,elem in ET.iterparse(osm_file):
        current = elem.tag
        #print current
        counts[current] += 1
        if elem.tag == 'node':  #part 1 test
            for tag in elem.iter("node"):
                temp=elem.attrib["id"]
                count = count +1
                id_.append(temp)
                #to list down all the keys present in the node
                #print elem.attrib.keys()
        #print "part 1 complete"        
        if elem.tag == 'tag':   #part 2 test
            for tag in elem.iter("tag"):
                key_k=elem.attrib["k"]
                key_v=elem.attrib["v"]
                # To make dictionary for all cuisines
                if (key_k=="cuisine"):
                    cuisine[key_v] += 1
                # To make dictiionary for all religions    
                elif(key_k=="religion"):
                    religion[key_v] += 1
                #k.append(key_k)
                #v.append(key_v)
        #print "part 2 complete"

        #part 3
        keys = key_type(elem, keys)
        
        if elem.tag== "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
        
            print "part 3 complete"

 #part 4 test
        el = shape_element(elem)
        count2=count2+1
        #print count
        if el:
            data.append(el)
            if pretty:
                fo.write(json.dumps(el, indent=2)+"\n")
                    #el.clear()
            else:
                fo.write(json.dumps(el) + "\n")
                #el.clear()
        if count2==50000:
            break


# print number of unique users
print len(unique_user)
#print max(zip(unique_user.values(),unique_user.keys()))
# printing most popular cuisine
print max(zip(cuisine.values(),cuisine.keys()))
# printing most popular religion
print max(zip(religion.values(),religion.keys()))

