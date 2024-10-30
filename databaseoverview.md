# Overview and quantitative comparisons with Web of Science and Scopus
*As of PubMed's 2022 version, 77GB*


## Item counts

**Available pmid's**
| Database | nr of pmids |
|----------|-------------|
| pubmed   | 23216441    |
| WoS      | 23046348    |
| Scopus   | 19326696    |


**Co-Occurences of PMID's**

| count    | nr of co-occurrences |
|----------|----------------------|
| 1        | 10                   |
| 2        | 8                    |
| 4        | 6                    |
| 17       | 5                    |
| 61       | 4                    |
| 429      | 3                    |
| 2396     | 2                    |
| 23213531 | 1                    |

- it shows that there are <3000 pmid with duplicates. A check of 13 pmid has shown that they are either from F1000, Plos Curr, or Wellcome Open Res and made use of the pubmed versioning system!

**citation counts to the PRISMA guidelines**
| Database | cit_count   |
|----------|-------------|
| my pubmed| 73352       |
| WoS      | ?           |
| Scopus   | ?           |
| GoogleS  | 112321      |


**Further notes**
- **Cochrane Reviews:** On August 2022, ~16k items from PubMed published in the Cochrane Journal were retrieved via entrez API. Cochrane states that there are currently 8892 systematic reviews in their database (see below). The reason for the deviation is because Cochrane does not count the different versions of the "same" systematic review. 


## References
09.02.2023: How comprehensive are the references in the pubmed database compared to WoS and Scopus? Compare...

1. ...the overall number of references in both databases per year
2. ...the combined amounts of reference count deviations between both databases (e.g. "there are 10k items with +5 references in WoS)

References in Pubmed:
```sql
create table ay_refs_comparison as
select aa.pmid, count(bb.fk_items) allrefs_pm,
count(case when bb.cited_pmid !='' then 1 else null end) xrefs_pm
from raw_items aa
left join raw_bibliography bb on aa.pk_items = bb.fk_items
group by aa.pmid
```
It seems that there are only 733k items which have at least one non-PubMed reference, meaning that PubMed is a highly connected universe with only few external links! From 2000 to 2022, there are ~105 million  references in PubMed, ~247 million references in Web Of Science and ~202 million references in Scopus based on the same items. This shows, that **Web of Science is the most comprehensive source of references** when restricted to PubMed data! In 2022, WoS offers about 11 mio more references and scopus around 8 mio more references than the PubMed Data.  

| Deviation  | PubMed-WoS | PubMed-Scopus |
|------------|------------|---------------|
| 6 to 100   |    0,2543% |       0,9515% |
|          5 |    0,0357% |       0,0393% |
|          4 |    0,0533% |       0,0331% |
|          3 |    0,0986% |       0,0351% |
|          2 |    0,2425% |       0,0479% |
|          1 |    1,1409% |       0,4024% |
|          0 |   16,0535% |      17,8549% |
|         -1 |    6,5071% |       5,4482% |
|         -2 |    4,0576% |       3,7936% |
|         -3 |    3,1518% |       2,9907% |
|         -4 |    2,6819% |       2,5496% |
|         -5 |    2,6946% |       2,6819% |
| -6 to -100 |   63,0282% |      63,1718% |

There are no deviations between WoS and PubMed for 16% of items in this set (~18% for Scopus and PubMed). There is a long-tail distribution of reference deviations towards both sides although heavily skewed towards WoS and Scopus having more references. In more than half of the items in the set, there are 6 to 100 more references in WoS or Scopus (both 63%) compared to PubMed. There is a neglectable amount of items with more references in PubMed compared to WoS or Scopus.
**Overall, it can be concluded, that PubMed's reference data provides less coverage compared to WoS and Scopus**

code
```sql
select aa.pubmed_wos deviation,
aa.devi_wos count_wos,
bb.devi_scp count_scp
from
(select pubmed_wos, count(pmid) devi_wos from kb_refs_comp_dist where pubmed_wos between -100 and 100 group by pubmed_wos) aa
left join
(select pubmed_scp, count(pmid) devi_scp from kb_refs_comp_dist where pubmed_scp between -100 and 100 group by pubmed_scp) bb
on aa.pubmed_wos=bb.pubmed_scp
order by aa.pubmed_wos desc;

```


## Pubdates and timestamps
*(as of 2022)*

Investigating timestamps reveals that all records have a database and medline timestamp, almost all have a official publication timestamp (97.14% on average). Only a fair amount has a timestamp for received (66.74%) and accepted (66.62%) and only slightly more than a third of pmid has a timestamp for revised (36.68% on average). For the latter three timestamp types, rates increased slightly over the duration. For exanoke in January 2020 from 63%, 34% and 61% to 71%, 39% and 72% in July of 2022. This shows that the data gets more comprehensive after some time, presumably due to data updates.

code
```sql
select
extract(year from d_p_medline) Jahr,
extract(month from d_p_medline) Monat, 
count(pmid) pmid_all,
ROUND((count(d_j_received)/count(pmid)::numeric),4) rate_received,
ROUND((count(d_j_revised)/count(pmid)::numeric),4) rate_revised,
ROUND((count(d_j_accepted)/count(pmid)::numeric),4) rate_accepted,
ROUND((count(d_j_published)/count(pmid)::numeric),4) rate_published,
ROUND((count(d_p_database)/count(pmid)::numeric),4) rate_added,
ROUND((count(d_p_medline)/count(pmid)::numeric),4) rate_medline
from sv_dates_study
where extract(year from d_p_medline) >= 2020
group by extract(year from d_p_medline), extract(month from d_p_medline)
order by Jahr desc, Monat desc;
```







