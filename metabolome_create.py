import requests
from neo4j.v1 import GraphDatabase, basic_auth

"""
######################################################################################
Requirements: neo4j.v1 package, requests
Code for creating metabolomic network from reactome metabolic pathways
Utilizes reactome api to generate networks in neo4j
User needs to supply neo4j (local or remote) username, password & neo4j server address
######################################################################################
"""

get_pathway_ancestors = 'https://reactome.org/ContentService/data/pathway/{reactome_id}/containedEvents'
get_reactome_id_information = 'https://reactome.org/ContentService/data/query/{reactome_id}'
get_reactome_enhanced_information = 'https://reactome.org/ContentService/data/query/enhanced/{reactome_id}'

CYPHER_Obtain_Metabolites = """
    MATCH (m:Metabolite) RETURN m.name as m_name,
    m.identifier as m_id
"""

CYPHER_Obtain_Pathways = """
    MATCH (p:Pathway) RETURN p.name as p_name,
    p.identifier as p_id
"""

CYPHER_Obtain_Reactome_Events = """
    MATCH (re:Reactome_Event) RETURN re.name as re_name,
    re.identifier as re_id
"""

CYPHER_Obtain_Enzymes = """
    MATCH (e:Enzyme) RETURN e.name as e_name,
    e.identifier as e_id
"""

CYPHER_Obtain_RE_Path = """
    MATCH (p:Pathway)<-[rel:IS_PART_OF]-(re:Reactome_Event)
    WHERE p.identifier contains '' and re.identifier contains ''
    RETURN p.identifier as p_id, re.identifier as re_id
"""

CYPHER_Obtain_RE_Metab_Out = """
    MATCH (m:Metabolite)<-[rel:EXITS]-(re:Reactome_Event)
    WHERE m.identifier contains '' and re.identifier contains ''
    RETURN m.identifier as m_id, re.identifier as re_id
"""

CYPHER_Obtain_RE_Metab_In = """
    MATCH (m:Metabolite)-[rel:ENTERS]->(re:Reactome_Event)
    WHERE m.identifier contains '' and re.identifier contains ''
    RETURN m.identifier as m_id, re.identifier as re_id
"""

CYPHER_Obtain_Path_Path = """
    MATCH (p1:Pathway)-[rel:IS_CHILD_OF]->(p2:Pathway)
    WHERE p1.identifier contains '' and p2.identifier contains ''
    RETURN p1.identifier as p1_id, p2.identifier as p2_id
"""

CYPHER_Obtain_Enzyme_Event = """
    MATCH (e:Enzyme)-[rel:IS_INVOLVED_IN]->(re:Reactome_Event)
    WHERE e.identifier contains '' and re.identifier contains ''
    RETURN e.identifier as e_id, re.identifier as re_id
"""

CYPHER_Create_Enzyme = """
    CREATE (e:Enzyme) SET e.name = "{name}", e.identifier = "{identifier}"
"""

CYPHER_Create_Pathway = """
    CREATE (p:Pathway) SET p.name = "{name}", p.identifier = "{identifier}"
"""

CYPHER_Create_Reactome_Event = """
    CREATE (re:Reactome_Event) SET re.name = "{name}",
    re.identifier = "{identifier}"
"""

CYPHER_Create_Metabolite = """
    CREATE (m:Metabolite) SET m.name = "{name}",
    m.identifier = "{identifier}"
"""

CYPHER_Create_Metabolite_In = """
    MATCH (m:Metabolite), (re:Reactome_Event)
    WHERE m.identifier = "{metab_id}" AND
    re.identifier = "{re_id}"
    CREATE (m)-[rel:ENTERS]->(re)
"""

CYPHER_Create_Metabolite_Out = """
    MATCH (m:Metabolite), (re:Reactome_Event)
    WHERE m.identifier = "{metab_id}" AND
    re.identifier = "{re_id}"
    CREATE (m)<-[rel:EXITS]-(re)
"""

CYPHER_Create_RE_Part_Of = """
    MATCH (re:Reactome_Event), (p:Pathway)
    WHERE re.identifier = "{re_id}" AND
    p.identifier = "{p_id}"
    CREATE (re)-[rel:IS_PART_OF]->(p)
"""

CYPHER_Create_Path_Parent_Of = """
    MATCH (p1:Pathway), (p2:Pathway)
    WHERE p1.identifier = '{p1_id}' AND
    p2.identifier = '{p2_id}'
    CREATE (p1)-[rel:IS_CHILD_OF]->(p2)
"""

CYPHER_Create_Enzyme_Involved_In = """
    MATCH (e:Enzyme), (re:Reactome_Event)
    WHERE e.identifier = '{e_id}' AND
    re.identifier = '{re_id}'
    CREATE (e)-[rel:IS_INVOLVED_IN]->(re)
"""

def analyze_json(json):
    if not isinstance(json, list):
        if 'code' in json.keys():
            if json['code'] == 404:
                return False
            else:
                return True
        else:
            return True
    else:
        return True

def create_reactome_dict(reactome_id):
    fin_dict = {reactome_id:{}}
    try:
        path_events = requests.get(get_reactome_id_information.format(reactome_id=reactome_id)).json()
        if analyze_json(path_events):
            if 'hasEvent' in path_events.keys():
                for item in path_events['hasEvent']:
                    react_id = item['stId']
                    react_name = item['displayName']
                    react_class = item['className']
                    event_info = requests.get(get_reactome_enhanced_information.format(reactome_id=react_id)).json()
                    metab_dict = {'input':[], 'output':[]}
                    if 'input' in event_info.keys():
                        for ie in event_info['input']:
                            if isinstance(ie, dict):
                                dict_element = {'Name':ie['displayName'],
                                                'React_ID':ie['stId'],
                                                'All_Names':ie['name'],
                                                'Class':ie['className']}
                                metab_dict['input'].append(dict_element)
                    if 'output' in event_info.keys():
                        for oe in event_info['output']:
                            if isinstance(oe, dict):
                                dict_element = {'Name':oe['displayName'],
                                                'React_ID':oe['stId'],
                                                'All_Names':oe['name'],
                                                'Class':oe['className']}
                                metab_dict['output'].append(dict_element)
                    catalyst_dict = dict()
                    if 'catalystActivity' in event_info.keys():
                        for item in event_info['catalystActivity']:
                            if 'physicalEntity' in item.keys():
                                cat_react_id = item['physicalEntity']['stId']
                                catalyst_dict.update({cat_react_id:{'Name':item['physicalEntity']['displayName'],
                                                    'All_Names':item['physicalEntity']['name'],
                                                    'Class':item['physicalEntity']['className']}})
                    fin_dict[reactome_id].update({react_id:{"react_name":react_name,
                                                            "react_class":react_class,
                                                            "metabolites":metab_dict,
                                                            "enzymes":catalyst_dict}})
            return fin_dict
        else:
            print "reactome id does not exist"
            fin_dict = None
            return fin_dict
    except:
        print "reactome id does not exist"
        fin_dict = None
        return fin_dict

def get_nodes(session, statement, node_type):
    nodes_dict = dict()
    records = session.run(statement)
    for r in records:
        node_id = r[node_type + "_id"]
        node_name = r[node_type + "_name"]
        nodes_dict.update({node_id:node_name})
    return nodes_dict

def get_rels(session, statement, first_r_type):
    rel_dict = dict()
    records = session.run(statement)
    for r in records:
        first = str(r[first_r_type + "_id"])
        second = str(r["re_id"])
        concat_id = first + "|" + second
        rel_dict.update({concat_id:"present"})
    return rel_dict

def get_path_path(session):
    p2p_dict = dict()
    records = session.run(CYPHER_Obtain_Path_Path)
    for r in records:
        child = r["p1_id"]
        parent = r["p2_id"]
        concat_id = child + "|" + parent
        p2p_dict.update({concat_id:"present"})
    return p2p_dict

def get_enzyme_re(session):
    e_re_dict = dict()
    records = session.run(CYPHER_Obtain_Enzyme_Event)
    for r in records:
        enzyme = r['e_id']
        re_id = r['re_id']
        concat_id = enzyme + "|" + re_id
        e_re_dict.update({concat_id:"present"})
    return e_re_dict

def get_pathway_name(path_id):
    try:
        json_dict = requests.get(get_reactome_id_information.format(reactome_id=path_id)).json()
        return json_dict['name']
    except:
        print "Error while processing pathway id"
        return "None"

def create_graph(react_dict, session):
    count_pathways = 0
    path_arr = []

    path_dict = get_nodes(session, CYPHER_Obtain_Pathways, "p")
    metab_dict = get_nodes(session, CYPHER_Obtain_Metabolites, "m")
    re_dict = get_nodes(session, CYPHER_Obtain_Reactome_Events, "re")
    enzyme_dict = get_nodes(session, CYPHER_Obtain_Enzymes, "e")

    # pathway_id|reactome_event_id
    # pathway<-is_part_of-reactome_event
    path_reactome_event = get_rels(session, CYPHER_Obtain_RE_Path, "p")
    
    # metab_id|reactome_event_id
    # metab<-exits-reactome_event
    metab_re_out = get_rels(session, CYPHER_Obtain_RE_Metab_Out, "m")
    
    # metab_id|reactome_event_id
    # metab-enters->reactome_event
    metab_re_in = get_rels(session, CYPHER_Obtain_RE_Metab_In, "m")

    # child_pathway_id|parent_pathway_id
    # childp-is_child_of->parentp
    path_path = get_path_path(session)

    # enzyme_id|reactome_event_id
    # enzyme-is_involved_in->reactome_event
    enzyme_re = get_enzyme_re(session)
    
    for key in react_dict.keys():
        if not key in path_dict.keys():
            path_name = get_pathway_name(key)
            if isinstance(path_name, list):
                act_path_name = path_name[0]
            else:
                act_path_name = path_name

            session.run(CYPHER_Create_Pathway.format(name=act_path_name.replace('"', ''),
                                                     identifier=key))
            path_dict.update({key:path_name})

        for event in react_dict[key].keys():
            if react_dict[key][event]['react_class'] == 'Reaction':
                event_id = event
                event_name = react_dict[key][event]['react_name']
                event_class = react_dict[key][event]['react_class']
                if not event_id in re_dict.keys():
                    session.run(CYPHER_Create_Reactome_Event.format(name=event_name.replace('"', '').encode('utf-8'),
                                                                    identifier=event_id.replace('"', '').encode('utf-8')))
                    re_dict.update({event_id:event_name})

                concat_rel = key + "|" + event_id
                if not concat_rel in path_reactome_event.keys():
                    session.run(CYPHER_Create_RE_Part_Of.format(re_id=event_id,
                                                                p_id=key))
                    re_dict.update({concat_rel:"present"})
                    
                for enzyme in react_dict[key][event]['enzymes'].keys():
                    enz_dict = react_dict[key][event]['enzymes'][enzyme]
                    enzyme_id = enzyme
                    enzyme_name = enz_dict['Name']
                    if not enzyme_id in enzyme_dict.keys():
                        session.run(CYPHER_Create_Enzyme.format(name=enzyme_name.replace('"', '').encode('utf-8'),
                                                                identifier=enzyme_id))
                        enzyme_dict.update({enzyme_id:enzyme_name})

                    concat_enzyme_rel = enzyme_id + "|" + event
                    if not concat_enzyme_rel in enzyme_re.keys():
                        session.run(CYPHER_Create_Enzyme_Involved_In.format(e_id=enzyme_id,
                                                                            re_id=event))
                        enzyme_re.update({concat_enzyme_rel:"present"})

                for key_2, items in react_dict[key][event]['metabolites'].iteritems():
                    if key_2 == 'input':
                        for m_input in items:
                            m_input_id = m_input['React_ID']
                            m_input_name = m_input['Name']

                            if not m_input_id in metab_dict.keys():
                                session.run(CYPHER_Create_Metabolite.format(name=m_input_name.replace('"', '').encode('utf-8'),
                                                                            identifier=m_input_id))
                                metab_dict.update({m_input_id:m_input_name})

                            input_concat_rel = m_input_id + "|" + event

                            if not input_concat_rel in metab_re_in.keys():
                                session.run(CYPHER_Create_Metabolite_In.format(metab_id=m_input_id,
                                                                               re_id=event))
                                metab_re_in.update({input_concat_rel:"present"})

                    if key_2 == 'output':
                        for m_output in items:
                            m_output_id = m_output['React_ID']
                            m_output_name = m_output['Name']

                            if not m_output_id in metab_dict.keys():
                                session.run(CYPHER_Create_Metabolite.format(name=m_output_name.replace('"', '').encode('utf-8'),
                                                                            identifier=m_output_id.replace('"', '').encode('utf-8')))
                                metab_dict.update({m_output_id:m_output_name})

                            output_concat_rel = m_output_id + "|" + event

                            if not output_concat_rel in metab_re_out.keys():
                                session.run(CYPHER_Create_Metabolite_Out.format(metab_id=m_output_id,
                                                                               re_id=event))
                                
                                metab_re_out.update({output_concat_rel:"present"})

            if react_dict[key][event]['react_class'] == 'Pathway':
                count_pathways = count_pathways + 1
                path_arr.append(event)
                path_id = event
                path_name = react_dict[key][event]['react_name']
                if not path_id in path_dict.keys():
                    session.run(CYPHER_Create_Pathway.format(name=path_name.replace('"', '').encode('utf-8'),
                                                             identifier=path_id.replace('"', '').encode('utf-8')))
                    path_dict.update({path_id:path_name})
                concat_pp_id = path_id + "|" + key
                if not concat_pp_id in path_path.keys():
                    session.run(CYPHER_Create_Path_Parent_Of.format(p1_id=path_id,
                                                                    p2_id=key))
                    path_path.update({concat_pp_id:"present"})
    return path_arr

def implement_reactome(reactome_id, session):
    r_dict = create_reactome_dict(reactome_id)
    if r_dict == None:
        arr = []
    else:
        arr = create_graph(r_dict, session)
    return arr

def recurse_reactome(arr, session):
    if len(arr) == 0:
        return True
    else:
        for item in arr:
            new_arr = implement_reactome(item, session)
            recurse_reactome(new_arr, session)

def create_metabolome(reactome_id, neo4j_web="", user="", password=""):
    if user == "" or password == "":
        driver = GraphDatabase.driver(neo4j_web)
        session = driver.session()
    else:
        driver = GraphDatabase.driver(neo4j_web, auth=basic_auth(user, password))
        session = driver.session()

    arr = [reactome_id]
    recurse_reactome(arr, session)

    
    
    
                        
                        
            
            
            

        
        
        
    
    
