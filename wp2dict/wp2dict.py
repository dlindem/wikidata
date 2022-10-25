import json, re, requests, time

# inlink expl # https://de.wikipedia.org/wiki/Marxistische_Wirtschaftstheorie
# apilink expl # https://de.wikipedia.org/w/api.php?action=parse&prop=text&page=Marxistische_Wirtschaftstheorie&format=json

allowed_lang = ['eu', 'es', 'en', 'fr', 'it', 'de', 'pt', 'ca', 'cs']

header_entries = ['wikidata', 'wikidatalink', 'source_page', 'instance_of', 'part_of', 'subclass_of']
for lang in allowed_lang:
    header_entries.append(lang)
    header_entries.append(lang+'_wikipedia')



with open('pagelinks.txt', 'r') as file:
    pagelinks = file.read().split('\n')
    print(str(pagelinks))

for pagelink in pagelinks:
    if pagelink.startswith('https://') == False:
        continue
    wlang = re.search(r'https://([^\.]+)\.', pagelink).group(1)
    pagetitle = re.search(r'wikipedia.org/wiki/(.*)', pagelink).group(1)
    print(wlang,pagetitle)
    gettexturl = 'https://'+wlang+'.wikipedia.org/w/api.php?action=parse&prop=text&page='+pagetitle+'&format=json'
    pagetext = requests.get(url=gettexturl).json()['parse']['text']['*']


    links = re.findall('href="/wiki/([^"]*)"', pagetext)
    #print(str(links))

    with open('output/'+pagetitle+'.'+wlang+'.csv', 'w') as outfile:
        outfile.write("\t".join(header_entries)+'\n')
        seenlinks = []
        for linkpagetitle in links:
            if re.search('[A-Z][a-z]+:', linkpagetitle): # "Spezial:", "Datei:", etc.
                continue
            if re.search('(disambiguation)', linkpagetitle): # exclude Disambiguation pages
                continue
            if re.search('[0-9]', linkpagetitle): # exclude page titles with numbers (pages describing days, years)
                continue
            if linkpagetitle in seenlinks:
                continue
            seenlinks.append(linkpagetitle)
            print(linkpagetitle)
            apiurl = 'https://www.wikidata.org/w/api.php?action=wbgetentities&sites='+wlang+'wiki&format=json&titles='+linkpagetitle
            print(apiurl)
            wdjsonsource = requests.get(url=apiurl)
            wdjson =  wdjsonsource.json()
            # with open('entity.json', 'w') as jsonfile:
            #     json.dump(wdjson, jsonfile, indent=2)
            takeresults = 1
            countresults = 0
            result = {'labels':{}, 'sitelinks':{}, 'part_of': [], 'subclass_of':[], 'instance_of':[]}
            for wdid in wdjson['entities']:
                if countresults == takeresults:
                    break
                if wdid.startswith("Q") == False:
                    continue
                countresults += 1

                if 'labels' in wdjson['entities'][wdid]:
                    for labellang in wdjson['entities'][wdid]['labels']:
                        result['labels'][labellang] = wdjson['entities'][wdid]['labels'][labellang]['value']

                if 'sitelinks' in wdjson['entities'][wdid]:
                    for langsite in wdjson['entities'][wdid]['sitelinks']:
                        result['sitelinks'][langsite.replace('wiki','')] = wdjson['entities'][wdid]['sitelinks'][langsite]['title']

                if 'claims' in wdjson['entities'][wdid]:
                    if 'P361' in wdjson['entities'][wdid]['claims']:
                        for claim in wdjson['entities'][wdid]['claims']['P361']:
                            result['part_of'].append('https://wikidata.org/wiki/'+claim['mainsnak']['datavalue']['value']['id'])
                    if 'P31' in wdjson['entities'][wdid]['claims']:
                        for claim in wdjson['entities'][wdid]['claims']['P31']:
                            result['part_of'].append('https://wikidata.org/wiki/'+claim['mainsnak']['datavalue']['value']['id'])
                    if 'P279' in wdjson['entities'][wdid]['claims']:
                        for claim in wdjson['entities'][wdid]['claims']['P279']:
                            result['subclass_of'].append('https://wikidata.org/wiki/'+claim['mainsnak']['datavalue']['value']['id'])


            #print(str(result))

            csvline = '\t'.join([
                        wdid,
                        'https://wikidata.org/wiki/'+wdid,
                        linkpagetitle,
                        ", ".join(result['instance_of']),
                        ", ".join(result['part_of']),
                        ", ".join(result['subclass_of'])
                    ])+'\t'
            for lang in allowed_lang:
                if lang in result['labels']:
                    langval = result['labels'][lang]+'\t'
                else:
                    langval = '\t'
                if lang in result['sitelinks']:
                    langval += 'https://'+lang+'.wikipedia.org/wiki/'+result['sitelinks'][lang]+'\t'
                else:
                    langval += '\t'
                csvline += langval
            outfile.write(csvline+"\n")
            time.sleep(0.2)
