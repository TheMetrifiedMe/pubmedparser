# Medline Retrieval and Analysis

This project represents the workflow of retrieving and analyzing data from the PubMed/Medline database. Instead of rebuilding the complete database, the focus lies on particular tasks that can not be done with the data offered by the [German Competence Network Bibliometrics](www.bibliometrie.info) or similar databases. These are:
- Retrieve the "Publication Type" created by PubMed/Medline
- ~~Retrieve the MeSH terms~~ (April 2024: MeSH terms now come with OpenAlex)
- Identify Cochrane Systematic Reviews
- Identify research about the Covid-19 pandemic

*Note that I spent susbtantial time in comparing this data against what is provided by Web of Science and Scopus. The three databases perform different on different categories, so a combination of the sources can improve the validity of bibliometric analysis. Feel free to get in touch if you need any help!* 

# How it works
The core tools can be found in ["PubmedParser.py"](PubmedParser.py). However, the parser writes data into a local PostgreSQL database which has to be set up manually. See ["databaseinititalization.md"](databaseinitialization.md) for an example and further info. The crawler retrieves data from PubMed's bulk download, unpacks and parses the XML in a RAM-friendly manner and writes the data into the database. While the SQL database highly speeds up analysis, it also takes time to commit the data blocks. Downloading, unpacking, writing for the 2023 version of PubMed takes ~50 hours on a common workstation.

Note that this tool does not use any common PubMed API's and is thus not bound to limitations or API keys. While the tools provided by PubMed are great for retrieving 


# Things to improve
- Improve the error handling. 
- logfiles/jobfiles could be entered into the database as well!


# Credits
Author: Alexander Schniedermann
[ORCID](https://orcid.org/0000-0003-2132-7419) | [mastodon](https://fediscience.org/@Aschniedermann)
The original project started in 2022 as part of my dissertation project.
