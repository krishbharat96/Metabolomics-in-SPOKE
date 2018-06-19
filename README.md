# Reactome Metabolomics in Neo4j
Utilizes Reactome Database in the automatic creation of Metbolomic hetnets for integration into SPOKE Medical Knowledge Network. This repository also contains a module for automatically downloading resources from the reactome web api and creating the metabolomic heterogenous network on your own, local version of Neo4j. Based on the location of the starting node in the Reactome ontology, the graph gets automatically generated on Neo4j (as shown below with the Tricarboxylic Acid cycle). In addition, if you would like to add an additional term's ontology from reactome to an already existing graph created from this module, you can do so by simply calling the create graph command (below) on that same neo4j graph file. The graph will still retain previously created nodes and will not duplicate nodes if already present. The module creates four node types:
  1. Reactome Pathway Node (e.g. TCA Cycle)
  2. Reactome Event Node (i.e. a metabolic event within a pathway -- e.g. conversion of citrate to isocitrate in TCA cycle)
  3. Reactome Metabolite Node (e.g. ATP)
  4. Reactome Enzyme Node (e.g. Succinate Dehydrogenase)

It also creates five relationship types:
  1. Pathway1 -IS_CHILD_OF-> Pathway2 (When Pathway2 is at a higher hierarchy within Reactome than Pathway1)
  2. Metabolite -ENTERS-> Reactome Event (When a metabolite is the input for a reactome event)
  3. Metabolite <-EXITS- Reactome Event (When a metabolite it the output for a reactome event)
  4. Reactome Event -IS_PART_OF-> Pathway (When a reactome event is involved in a Pathway)
  5. Enzyme -IS_INVOLVED_IN-> Reactome Event (When an enzyme is involved in a reactome event)

Module requirements: neo4j-driver package (can obtain easily via pip install neo4j-driver or through conda), requests package, working version of Neo4j on local device (or access to remote version of Neo4j)

Using this Module:
  1. Install the module to your computer:
  
  ```
  wget https://raw.githubusercontent.com/krishbharat96/Metabolomics-in-SPOKE/master/metabolome_create.py
  ```
  
  2. Select reactome identifier to create metabolomic hetnets from (For example: 'R-HSA-71403' or Tricarboxylic Acid Cycle in Homo sapiens).
  3. Import the module, set neo4j webpage information and create the metabolome:
  
  ```
  import metabolome_create as mc
  mc.create_metabolome('R-HSA-71403', neo4j_web="bolt://localhost:11001", user="user", password="password")
  ```
  
  4. Start using the network on Neo4j for Pathway Analysis!

Here is a sample hetnet created for the TCA cycle using this module:

![alt text](https://raw.githubusercontent.com/krishbharat96/Metabolomics-in-SPOKE/master/TCA_Cycle_Reactome_New.png) 

  
