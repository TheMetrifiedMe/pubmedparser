# -*- coding: utf-8 -*-
# Python Module PubmedParser
"""
Created on Mon May  9 15:17:38 2022
@author: alexs
License: CC0
"""

import xml.etree.ElementTree as ET
import psycopg2
from urllib.request import urlopen
from tempfile import NamedTemporaryFile
import gzip
from datetime import datetime
from datetime import timedelta
import json
from dateutil.parser import parse
import time
from databasecredentials import database_credentials

conn = database_credentials()
current_id = 0
current_url = ""
var_lastSet = False
nrArticles = 0
setduration = ""
updatemode = False
overwrites = 0
uniqueitemid = 0


def globalpurge():
    global current_id
    global current_url
    current_id = 0
    current_url = ""

    global setduration
    global overwrites


    setduration = ""
    overwrites = 0
    pass
    
    
def saveDict():
    global current_id
    global current_url
    global nrArticles
    global setduration
    global updatemode
    global overwrites
    global uniqueitemid
            
    setdict = {
        "set_ID": current_id,
        "url":current_url,
        "nrArticles":nrArticles,
        "nrOverwrites":overwrites,
        "parsingtime":setduration,
        "wasLastSet":var_lastSet,
        "lastitemid":uniqueitemid
        }

    if updatemode == False:
        with open( "parsingdicts.json", 'a' ) as f: 
            f.write("\n"+ json.dumps(setdict))
    else:
        with open( "parsingdicts_updates.json", 'a' ) as f: 
            f.write("\n"+ json.dumps(setdict))
      
def readLastDictForNextUrl():
    global current_id 
    global current_url
    global updatemode
    global var_lastSet
    global uniqueitemid
    
    if updatemode == False:
        #Normales Parsi ng der PubMed Bulk Baseline
        with open( "parsingdicts.json", 'r' ) as f:
            for line in f:
                pass
            lastdict = json.loads(line)
            current_id = lastdict.get("set_ID") -1
            uniqueitemid = lastdict.get("lastitemid")
     
            idstring = str(current_id).zfill(4)
            current_url = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n" + idstring +".xml.gz"
            if current_id == 1050:
                print(f"id is {current_id}, last parsable set")
                var_lastSet = True
    else:
        #Parsing der Updatefiles
        with open( "parsingdicts_updates.json", 'r' ) as f:
            for line in f:
                pass
            lastdict = json.loads(line)
            current_id = lastdict.get("set_ID") +1
            uniqueitemid = lastdict.get("lastitemid")
     
            idstring = str(current_id).zfill(4)
            current_url = "https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed24n" + idstring +".xml.gz"
            if current_id == 1500:
                print(f"id is {current_id}, last parsable set")
                var_lastSet = True                          
    pass

#Unzip function
def get_xml(zipurl):
    with urlopen(zipurl) as zipresp, NamedTemporaryFile() as tfile:
        tfile.write(zipresp.read())
        tfile.seek(0)
        with gzip.open(tfile, 'rb') as f:
            currentxml = f.read().decode('utf-8')
            return currentxml

def parsestuff(article):
    pmid = ""
    doi = ""
    modeldescr = ""
    titletext = ""
    abstext = ""
    pmid_version = ""
    journal_abbrev = "" 
    j_nlm_id_unique = "" 
    global updatemode
    global uniqueitemid
    
    fpk_item = uniqueitemid


    #get the identifiers PMID and DOI    
    pmid = article.findall('MedlineCitation')[0].findall('PMID')[0].text
    pmid_version = article.findall('MedlineCitation')[0].findall('PMID')[0].get('Version')

    idset = article.findall('PubmedData')[0].findall('ArticleIdList')[0].findall("ArticleId")
    for singelid in idset:
        if singelid.get("IdType") == "doi":
            doi = singelid.text
            break
        else:
            pass

    
    #get timestamp for PubMed Model (print, electronic etc.) NOTE: This only saves the last one, but it seems that there is only "print" in the xml files
    #I used this codde at all because otherwise I would get multiple timestamps for each item that are inseparable
    for pubmodel in article.iter("Article"):
        modeldescr =  pubmodel.get("PubModel")
        
        try:
            model_elocation = pubmodel.findall('ELocationID')[0]
            doi_pubmodel = ""
            if model_elocation.get("EIdType") == "doi" and model_elocation.get("ValidYN") == "Y":
                doi_pubmodel = model_elocation.text
        except:
            doi_pubmodel = ""

        
        for timeinfo in pubmodel.iter("PubDate"):
            try:
                jou_d_type = "journaldate_" + str(modeldescr)
            except:
                jou_d_type = "journaldate_None"
            try:
                jou_d_year = timeinfo.find("Year").text
            except:
                jou_d_year = ""
            try:    
                jou_d_month = timeinfo.find("Month").text
            except:
                 jou_d_month = ""
            try:    
                jou_d_day = timeinfo.find("Day").text
            except:
                jou_d_day = ""
            try:    
                jou_d_season = timeinfo.find("Season").text
            except:
                jou_d_season = ""
                
            if jou_d_year != "" and jou_d_month != "" and jou_d_day != "":
                try:
                    jou_d_timestamp = parse(f"{jou_d_year}-{jou_d_month}-{jou_d_day}").strftime('%Y-%m-%d')
                except:
                    pass
            else:
                try:
                    jou_d_timestamp = create_valid_date(jou_d_year,jou_d_month,jou_d_day)
                except:
                    jou_d_timestamp = ""
                
            write_dates(jou_d_type, jou_d_timestamp, jou_d_year,jou_d_month,jou_d_day, jou_d_season, pmid_version)


    
    # get the title
    for title in article.iter("ArticleTitle"):
        try:
            #itertext() is used and should be used in other cases, since the text fields can have additional xml fields, e.g. for formatting super- and subscript numbers!
            titletext = "".join(title.itertext())
        except:
            titletext = "NULL"
   
    # get the abstract
    for abstract in article.iter("Abstract"):
        try:
            abstext = "".join(abstract.itertext())
        except:
            abstext = "NULL"
            
    # get the journal info and add cochrane to types
    # INFO: The type writer could become a problem if a PK-FK constraints is checked before the commit!
    for sourceinfo in article.iter("MedlineJournalInfo"):
        journal_abbrev = sourceinfo.find("MedlineTA").text
        j_nlm_id_unique = sourceinfo.find("NlmUniqueID").text
        if j_nlm_id_unique == "100909747":
            write_types("Cochrane Systematic Review", fpk_item)
        else:
            pass 

    write_item(pmid, doi, titletext, abstext, modeldescr, doi_pubmodel, pmid_version, journal_abbrev, j_nlm_id_unique, fpk_item)
    uniqueitemid +=1

#relational data 
    #publication types
    for ptypes in article.iter("PublicationType"):
        try:
            pubtypes = ptypes.text
            write_types(pubtypes, fpk_item)
        except:
            pass
    
    #mesh Headings
    for meshes in article.iter("MeshHeading"):
        meshDescr = meshes.find("DescriptorName").text
        hascorona = IsMeshCorona(meshDescr)
        meshDescrMT = meshes.find("DescriptorName").attrib["MajorTopicYN"]
        try:
            if len(meshes) == 1:
                qualText = ""
                qualMT = ""
            else: 
                for meshQual in meshes.iter("QualifierName"):
                    qualText = meshQual.text
                    qualMT = meshQual.attrib["MajorTopicYN"]
            write_meshes(meshDescr,meshDescrMT,qualText,qualMT,hascorona,fpk_item)
        except:
            pass
            
       

    # Date catcher for the PubMed Dates Which reflect the PubMed History (first entry, finished entry, updates etc.)    
    for pubdates in article.iter("PubMedPubDate"):
        try:
            pub_d_datetype = pubdates.get("PubStatus")
        except:
            pub_d_datetype = ""
        try:
            pub_d_year = pubdates.find("Year").text
        except:
            pub_d_year = ""
        try:
            pub_d_month = pubdates.find("Month").text
        except:
            pub_d_month = ""
        try:
            pub_d_day = pubdates.find("Day").text
        except:
            pub_d_day = ""
        try:    
           pub_d_season = pubdates.find("Season").text
        except:
           pub_d_season = ""
           
        if pub_d_year != "" and pub_d_month != "" and pub_d_day != "":
            try:
                pub_d_string = parse(f"{pub_d_year}-{pub_d_month}-{pub_d_day}").strftime('%Y-%m-%d')
            except:
                try:
                    pub_d_string = create_valid_date(pub_d_year,pub_d_month,pub_d_day)
                except:
                    pub_d_string = ""
        else:
            try:
                pub_d_string = create_valid_date(pub_d_year,pub_d_month,pub_d_day)
            except:
                pub_d_string = ""
       
        write_dates(pub_d_datetype, pub_d_string, pub_d_year, pub_d_month, pub_d_day, pub_d_season, fpk_item)
    
        
        
    #get references (citingpmid, citedpmid and the unstructured reference string)
    for reference in article.iter("Reference"):
        try:
            for elem in reference.iter("Citation"):
                reference_string = "".join(elem.itertext())
        except:
            reference_string = ""
        
        cited_pmid = ""
        for each_id in reference.iter("ArticleId"):
            if each_id.get("IdType") == "pubmed":
                cited_pmid = each_id.text
            else:
                cited_pmid = ""

        write_refs(cited_pmid, reference_string, fpk_item)
        

        
        
        
def write_refs(cited_pmid = "", reference_string = "", fk_item = 0):
    global conn

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO raw_bibliography values (%s,%s,%s)', (cited_pmid, reference_string, fk_item))
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e) 
    finally:
        cur.close() 
        
        
def write_dates(datetype = "", datevalue = "", year = "", month = "", day = "", season = "", fk_item = 0):
    global conn

    
    try:
        cur = conn.cursor()
        cur.execute("""INSERT INTO raw_pubdates VALUES (%s, TO_DATE(%s, 'YYYY-MM-DD'), %s,%s,%s,%s,%s)""", (datetype, datevalue, str(year), str(month), str(day), str(season), fk_item))
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e) 
    finally:
        cur.close()

def write_item(pmid, doi, titletext, abstext, modeldescr, doi_pubmodel, pmid_version = "0", journal_abbrev = "",j_nlm_id_unique = "", fk_item =0):
    global conn

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO raw_items VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (str(pmid), doi, modeldescr,current_id, doi_pubmodel, titletext, abstext, pmid_version, journal_abbrev,j_nlm_id_unique, fk_item))
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e)
    finally:
        cur.close()
    
    
def write_types(pubtype = "", fk_item = 0):
    global conn

    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO raw_ptypes VALUES (%s,%s)', (pubtype, fk_item))
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e)    
    finally:
        cur.close()

def write_meshes(meshDescr = "",meshDescrMT = "",qualText = "",qualMT ="", has_corona = "0", fk_item = 0):
    global conn

    try:
        global conn
        cur = conn.cursor()
        cur.execute('INSERT INTO raw_meshinfo VALUES (%s,%s,%s,%s,%s,%s)', (meshDescr, qualText, to_bool(meshDescrMT), to_bool(qualMT), has_corona, fk_item))
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e)
    finally:
        cur.close()
        
def checkAndDelete(pmid):
# This function produces a lot of table scans und makes everything super slow!
    global conn
    global overwrites
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM items WHERE pmid = %s', (str(pmid),))
        p = cur.fetchone()
        if p != None:
            cur.execute('DELETE FROM items WHERE pmid = %s', (str(pmid),))
            cur.execute('DELETE FROM meshinfo WHERE pmid = %s', (pmid,))
            cur.execute('DELETE FROM ptypes WHERE pmid = %s', (str(pmid),))
            cur.execute('DELETE FROM pubdates WHERE pmid = %s', (pmid,))
            print("kicked some stuff out", end = "; ")
            overwrites +=1
    except:
        pass
    finally:    
        cur.close()
        

def to_bool(string):
    if string == "Y":
        return True
    else:
        return False

#Deal with different date schemes, check dates fro range and neglect empty fields
def create_valid_date(year = "", month = "", day = "", season = ""):
    if year != "" and month != "":
        if day == "":
            day = "01"
        else:
            pass
        
        
        isdatevalid = False
        while isdatevalid == False and int(day) >0:
            
            try:
                validdate = parse(f"{year}-{month}-{day}")
                isdatevalid = True
            except:
                day = str(int(day) -1)
                isdatevalid = False
    
        if isdatevalid == True:
            endstring = validdate.strftime('%Y-%m-%d')
        else:
            endstring = ""

    
    elif year != "" and month == "" and season == "":
        endstring = year
    elif year != "" and month == "" and season != "":
        endstring = year + season_to_month(season)
    else:
        endstring = ""
    return endstring


def season_to_month(season):
    relations = {
    	"spring":"-03-21",
    	"summer":"-06-21",
    	"autumn":"-09-21",
    	"fall":"-09-21",
    	"winter":"-12-21"
        }
    try:
        newstring = relations.get(season.lower(), "")
    except:
        newstring = ""
    return newstring

def IsMeshCorona(heading):
    infestedmeshs = [
        "coronavirus 3c proteases",
        "coronavirus envelope proteins",
        "coronavirus m proteins",
        "coronavirus nucleocapsid proteins",
        "coronavirus papain-like proteases",
        "coronavirus protease inhibitors",
        "coronavirus rna-dependent rna polymerase",
        "covid-19",
        "covid-19 nucleic acid testing",
        "covid-19 serological testing",
        "covid-19 testing",
        "covid-19 vaccines",
        "receptors, coronavirus",
        "sars-cov-2",
        "spike glycoprotein, coronavirus"
        ]
    if heading.lower() in (infestedmesh.lower() for infestedmesh in infestedmeshs):
        return '1'
    else:
        return '0'


# Does the sql connection stuff and calls the mainParser function for each Article
def main_Parser(a):
    global conn
    global userdata
    global var_lastSet
    global overwrites
    global nrArticles
    global current_id
    
    try:
        conn = database_credentials()
        root = ET.fromstring(a)     
        for article in root.findall('PubmedArticle'):
            parsestuff(article)
            nrArticles += 1
        conn.commit()        
    except psycopg2.OperationalError as e:
        print('Unable to connect!\n{0}').format(e)
        conn.rollback()
        var_lastSet = True
        print(f"finished due to connection error. Rollback. Recrawl {var_lastSet}")
    finally:
        conn.close()
        print("", end = ".")
        if current_id % 10 == 0:
            print("")
            print(datetime.now().strftime("%H:%M:%S") + f" | {nrArticles} items commited, last set was {current_id}", end = "")


# envelope function, loops and calls the various functions: get an url, get its xml, parse the xml report stuff to globalfile
def mainfunction(duration):
    global var_lastSet
    global setduration
    global current_url
    
    endtime = timedelta(minutes = duration) + datetime.now()
    print("start job until: ",format(endtime), "minutes")

    while var_lastSet == False:   
        try:
            starttime = datetime.now()
            readLastDictForNextUrl()   
            nexturl = current_url
            main_Parser(get_xml(nexturl))
        except Exception as e:
            print("ERROR! mainfunction will end: " + format(datetime.now()))
            print(e)
            var_lastSet = True
        finally:
            setduration = format(datetime.now() - starttime)
            saveDict()
            globalpurge()
            
        if datetime.now() > endtime:
            var_lastSet = True
            print("finished due to job time")
            
            
            
            
# Loads a PMID List from a JSON into python and crawls its contents from the server. Use id_for_fetchedset to assign a "version number"           
def efetcher_single_pmids(name_of_fetchedset ,id_for_fetchedset):
    global current_id
    global var_lastSet
    current_id = id_for_fetchedset
    setcount = 0
    restcount = 0
    var_lastSet == False
    
    baseurl = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id="
    endurl = "&rettype=xml&tool=pubmedparser&email=schniedermann@dzhw.eu"
    # between them comes a list of pmid's, separated by comma, e.g. 27558065,27466125,27127816,26842040
    # fetch no more than 200 articles per attempt!
    
    habefertig = False
    while habefertig == False:
        with open(name_of_fetchedset, 'r' ) as f:
                for line in f:
                    pass
                lastlist = list(json.loads(line))
                if len(lastlist) == 0:
                    habefertig = True
                    setcount = setcount + len(lastlist)
                elif len(lastlist) > 200:
                    newset = lastlist[:200]
                    restset = lastlist[200:]
                    setcount += 200
                    restcount = len(restset)
                else:
                    newset = lastlist
                    restset = []
                    habefertig = True
                    print("Last set")
         
        uidliststring = ','.join(str(e) for e in newset)  
        fetchurl = baseurl + uidliststring + endurl
    
        with urlopen(fetchurl) as directxml, NamedTemporaryFile() as tfile:
            tfile.write(directxml.read())
            tfile.seek(0)
            fetchedrecord = tfile.read()
    

        # Pass to parser and let him do his magic. Update the JSON and print if applicable
        main_Parser(fetchedrecord)
        if var_lastSet == False:
            with open(name_of_fetchedset, 'w' ) as f: 
                f.write(json.dumps(restset))
            if setcount % 10000 == 0:
                print(f"finished some {setcount} records, {restcount} records left")
            else:
                pass
        else:
            print("mainParser Error: end fetch loop")
            habefertig = True
        
        time.sleep(2)


#efetcher_single_pmids("cochrane_dict.json",9005)

# efetch URL for checking purpose: 
# https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=36434555&retmode=xml       

# def efetcher_add_lists(file, table = '', valuelist=''):
#     #This tool is designed to read an PMID List of an XML document that results from a PubMed search. It was originally developed to get a list of Cochrane Systematic Reviews
#     #global userdata
#     global conn
#     global current_id
    
#     tree = ET.parse(file)
#     root = tree.getroot()
#     idlist = root.find('IdList')
    
#     ptype = valuelist[0]
#     current_id = valuelist[1]
#     pmid_version = valuelist[2]
    
    
#     conn = database_credentials()
#     try:
#         for eachid in idlist:
#             pmid = eachid.text
#             write_types(pmid, ptype, pmid_version)

#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         print(e + ", rollback")
#     finally:
#         conn.close()
#efetcher_add_lists('cochrane_reviews_esearch.xml','',['Cochrane Systematic Review', 9999, 0])


