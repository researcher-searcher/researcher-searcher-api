import requests
import json
import pprint
import pandas as pd
from loguru import logger
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect

api_url = 'http://localhost:8000'
pp = pprint.PrettyPrinter(indent=4)

test_text1 = (
    "Funding is available from MRC’s Infections and Immunity Board to provide large, "
    "long-term and renewable programme funding for researchers working in the area of "
    "infections and immunity. There is no limit to the funding you can request. This "
    "funding opportunity runs three times every year."
)
test_text2 = (
    "Funding is available from MRC’s Neurosciences and Mental Health Board to support new partnerships between "
    "researchers in the area of neurosciences and mental health. Funding varies widely for partnerships lasting "
    "between one and five years. This funding opportunity runs three times every year."
)
test_text3 = (
    "We have implemented efficient search methods and an application programming interface, to create fast and convenient"
    " functions to utilize triples extracted from the biomedical literature by SemMedDB."
)
test_text4 = (
    "Ankyrin-R provides a key link between band 3 and the spectrin cytoskeleton that helps to maintain the highly "
    "specialised erythrocyte biconcave shape. Ankyrin deficiency results in fragile spherocytic erythrocytes with "
    "reduced band 3 and protein 4.2 expression. We use in vitro differentiation of erythroblasts transduced with shRNAs "
    "targeting the ANK1 gene to generate erythroblasts and reticulocytes with a novel ankyrin-R ‘near null’ human "
    "phenotype with less than 5% of normal ankyrin expression. Using this model we demonstrate that absence of ankyrin "
    "negatively impacts the reticulocyte expression of a variety of proteins including band 3, glycophorin A, spectrin, "
    "adducin and more strikingly protein 4.2, CD44, CD47 and Rh/RhAG. Loss of band 3, which fails to form tetrameric "
    "complexes in the absence of ankyrin, alongside GPA, occurs due to reduced retention within the reticulocyte membrane "
    "during erythroblast enucleation. However, loss of RhAG is temporally and mechanistically distinct, occurring "
    "predominantly as a result of instability at the plasma membrane and lysosomal degradation prior to enucleation. "
    "Loss of Rh/RhAG was identified as common to erythrocytes with naturally occurring ankyrin deficiency and "
    "demonstrated to occur prior to enucleation in cultures of erythroblasts from a hereditary spherocytosis patient "
    "with severe ankyrin deficiency but not in those exhibiting milder reductions in expression. The identification of "
    "prominently reduced surface expression of Rh/RhAG in combination with direct evaluation of ankyrin expression using "
    "flow cytometry provides an efficient and rapid approach for the categorisation of hereditary spherocytosis arising "
    "from ankyrin deficiency."
)
test_text5 = (
    "Risk factors for breast cancer"
)

test_text6 = "neuroscience"

#https://pubmed.ncbi.nlm.nih.gov/25751625/
# compare this to the copy/paste text - find expertise results
# https://research-information.bris.ac.uk/en/concepts/copypaste/
test_text7 = (
    "Genome-wide association studies (GWAS) and large-scale replication studies have identified common "
    "variants in 79 loci associated with breast cancer, explaining ∼14% of the familial risk of the disease. "
    "To identify new susceptibility loci, we performed a meta-analysis of 11 GWAS, comprising 15,748 breast "
    "cancer cases and 18,084 controls together with 46,785 cases and 42,892 controls from 41 studies "
    "genotyped on a 211,155-marker custom array (iCOGS). Analyses were restricted to women of European "
    "ancestry. We generated genotypes for more than 11 million SNPs by imputation using the 1000 Genomes "
    "Project reference panel, and we identified 15 new loci associated with breast cancer at P < 5 × 10(-8). "
    "Combining association analysis with ChIP-seq chromatin binding data in mammary cell lines and ChIA-PET "
    "chromatin interaction data from ENCODE, we identified likely target genes in two regions: SETBP1 at "
    "18q12.3 and RNF115 and PDZK1 at 1q21.1. One association appears to be driven by an amino acid "
    "substitution encoded in EXO1."
)

def person_query(text):
    logger.info(text)
    url = f'{api_url}/search/'
    params = {"query":text,"method":"person"}
    res = requests.get(url,params).json()
    #logger.info(res['res'])
    df = pd.json_normalize(res['res'])
    logger.info(f'\n{df.head()}')

def vec_query(text):
    logger.info(text)
    url = f'{api_url}/search/'
    params = {"query":text,"method":"vec"}
    res = requests.get(url,params).json()
    logger.info(res['res'])
    df = pd.json_normalize(res['res'])
    logger.info(f'\n{df.head()}')

if __name__ == "__main__":
    #person_query(test_text7)
    vec_query(test_text7)