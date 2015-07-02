from lxml import html
import requests
import re
import csv

output_filename = 'NGSS_PEs.csv'
base_url = 'http://www.nextgenscience.org'    

# Utilitiy functions
def dict_get(dct, key, default_value=''):
    v = dct.get(key)
    if (v==None):
        return default_value
    return v

def list_of_pe_urls(base_url='http://www.nextgenscience.org'):
    "Scrape PEs organized by DCI to get URLs of PEs"
    page = requests.get(base_url+'/search-standards-dci')
    tree = html.fromstring(page.text)
    # Build list of relative URLs
    pe_urls = tree.xpath('//table[@class="standard-table"]//td//a/@href')
    # Sort the URLs stably by grade level by 2nd character in string:
    def grade_level(url):
        # url[1] is 2nd character, 1st after /
        if url[1:4]=='k-2': return '3' # Stable sorting will put this before 3rd grade
        if url[1]=='k': return '0'
        if url[1:3]=='ms': return '6'
        if url[1:3]=='hs': return '9'
        return url[1]
    pe_urls = sorted(pe_urls, key=grade_level)
    return pe_urls
    
#relative_pe_urls = list(set(list_of_pe_urls())) # Uncomment to grab fresh copy of array
#relative_pe_urls = ['/kps2-motion-stability-forces-interactions', '/kps3-energy', '/kls1-molecules-organisms-structures-processes', '/kess2-earth-systems', '/kess3-earth-human-activity', '/1ps4-waves-applications-technologies-information-transfer', '/1ls1-molecules-organisms-structures-processes', '/1ls3-heredity-inheritance-variation-traits', '/1ess1-earth-place-universe', '/2ps1-matter-interactions', '/2ls2-ecosystems-interactions-energy-dynamics', '/2ls4-biological-evolution-unity-diversity', '/2ess1-earths-place-universe', '/2ess2-earth-systems', '/k-2ets1-engineering-design', '/3ps2-motion-stability-forces-interactions', '/3ls1-molecules-organisms-structures-processes', '/3ls2-ecosystems-interactions-energy-dynamics', '/3ls3-heredity-inheritance-variation-traits', '/3ls4-biological-evolution-unity-diversity', '/3ess2-earth-systems', '/3ess3-earth-human-activity', '/3-5ets1-engineering-design', '/4ps3-energy', '/4ps4-waves-applications-technologies-information-transfer', '/4ls1-molecules-organisms-structures-processes', '/4ess1-earth-place-universe', '/4ess2-earth-systems', '/4ess3-earth-human-activity', '/5ps1-matter-interactions', '/5ps2-motion-stability-forces-interactions', '/5ps3-energy', '/5ls1-molecules-organisms-structures-processes', '/5ls2-ecosystems-interactions-energy-dynamics', '/5ess1-earth-place-universe', '/5ess2-earth-systems', '/5ess3-earth-human-activity', '/msps1-matter-interactions', '/msps2-motion-stability-forces-interactions', '/msps3-energy', '/msps4-waves-applications-technologies-information-transfer', '/msls1-molecules-organisms-structures-processes', '/msls2-ecosystems-interactions-energy-dynamics', '/msls3-heredity-inheritance-variation-traits', '/msls4-biological-evolution-unity-diversity', '/msess1-earth-place-universe', '/msess2-earth-systems', '/msess3-earth-human-activity', '/msets1-engineering-design', '/hsps1-matter-interactions', '/hsps2-motion-stability-forces-interactions', '/hsps3-energy', '/hsps4-waves-applications-technologies-information-transfer', '/hsls1-molecules-organisms-structures-processes', '/hsls2-ecosystems-interactions-energy-dynamics', '/hsls3-heredity-inheritance-variation-traits', '/hsls4-biological-evolution-unity-diversity', '/hsess1-earth-place-universe', '/hsess2-earth-systems', '/hsess3-earth-human-activity', '/hsets1-engineering-design']
relative_pe_urls = ['/kps3-energy']
#print(relative_pe_urls.__repr__()) # Used to generate the line above

# Add base URLs to get full URLs
pe_urls = list(map(lambda x: base_url+x, relative_pe_urls))

# Show our results
#for url in pe_urls:
#    print(url)

# regular expressions    
_p_whitespace = re.compile("(\t|\n|\xa0)+", flags=re.MULTILINE|re.DOTALL)  
_p_doublespace = re.compile("  ", flags=re.MULTILINE|re.DOTALL)
_p_desc_cs_ab = re.compile(r"(?P<description>[^\[\]]*)\s*(?:\[Clarification Statement:\s*(?P<clarification_statement>[^\[\]]*)\])?\s*(?:\[Assessment Boundary:\s*(?P<assessment_boundary>[^\[\]]*)\])?")    
def pes_from_relative_url(relative_pe_url, base_url='http://www.nextgenscience.org'):    
    def record_from_pair(x):
        "helper function to turn pair into useful hash"
        pe_code, pe_description = x
        pe_description = pe_description.strip()
        # Expand PE code into parts
        parts = pe_code.split('-')
        if len(parts)==3:
            grade, dci, pe_number = parts
        elif len(parts)==4:
            begin_grade, end_grade, dci, pe_number = parts
            grade = '-'.join([begin_grade, end_grade])
        else:
            print("* Error: Unexpected number of parts to PE code.")
            exit()            
        # Expand PE description into parts        
        match = _p_desc_cs_ab.search(pe_description)
        if (match):
            dct = match.groupdict()
        else:
            dct = dict() # Empty dictionary
        return { 
        "PE Code": pe_code,
        "Grade": grade,
        "DCI": dci,
        "PE Number": pe_number,
        "Full PE Description": pe_description.strip(),
        "PE Description": dict_get(dct,'description').strip(),
        "Clarification Statement": dict_get(dct,'clarification_statement').strip(),
        "Assessment Boundary": dict_get(dct,'assessment_boundary').strip(),
        }
    print("Scraping", relative_pe_url)
    page = requests.get(base_url+relative_pe_url)
    tree = html.fromstring(page.text)
    # The page has a stupid structure with 3 different tables depending on the option clicked. div.field-name-body contains the first copy of the table
    tr = tree.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-body ")]//table[@class="standard"]//tr[@class="row2"]//table//tr')
    unprocessed_pe_code = tree.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-body ")]//table[@class="standard"]//tr[@class="row2"]//table//tr/th/text()')
    processed_pe_code = list(map(lambda s: s.rstrip('.'), unprocessed_pe_code))    
    unprocessed_pe_desc = tree.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-body ")]//table[@class="standard"]//tr[@class="row2"]//table//tr/td')
    somewhat_processed_pe_desc = list(map(lambda node: ''.join(node.itertext()), unprocessed_pe_desc))
    processed_pe_desc = list(map(lambda s: _p_doublespace.sub(" ",_p_whitespace.sub(" ", s)),somewhat_processed_pe_desc))  
    return list(map(record_from_pair, zip(processed_pe_code, processed_pe_desc)))    

    #return list(zip(unprocessed_pe_code, unprocessed_pe_desc))

pe_list = []
for relative_pe_url in relative_pe_urls:
    rv = pes_from_relative_url(relative_pe_url)
    print(rv)
    pe_list.extend(rv)

def output_csv(output_filename, pe_list):
    with open(output_filename, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'Grade',
            'DCI',
            'PE Number',
            'PE Code',
            'PE Description',
            'Clarification Statement',
            'Assessment Boundary',
            'Full PE Description',
            ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pe_list)
output_csv(output_filename, pe_list)