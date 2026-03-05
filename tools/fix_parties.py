import pandas as pd
import requests
import concurrent.futures

PARTIES = [
    'Socialdemokratiet', 'Venstre', 'Moderaterne', 'Socialistisk Folkeparti',
    'Danmarksdemokraterne', 'Liberal Alliance', 'Det Konservative Folkeparti',
    'Konservative', 'Enhedslisten', 'Dansk Folkeparti', 'Radikale Venstre',
    'Alternativet', 'Nye Borgerlige', 'Borgernes Parti', 'Frie Grønne'
]

def fetch_party(url):
    if not isinstance(url, str) or not url.startswith('http'): 
        return url, 'Unknown'
    try:
        r = requests.get(url, timeout=5)
        text = r.text
        # DR sometimes has the party in the title tag: <title>Trine Birk Andersen - Socialdemokratiet - DR</title>
        import re
        m = re.search(r'<title>(.*?)</title>', text)
        if m:
            title = m.group(1)
            for p in PARTIES:
                if p in title:
                    return url, p
                    
        # Fallback to search in html
        first_idx = len(text)
        best_party = 'Unknown'
        for p in PARTIES:
            idx = text.find(p)
            if idx != -1 and idx < first_idx:
                first_idx = idx
                best_party = p
        return url, best_party
    except Exception as e:
        return url, 'Unknown'

def main():
    df = pd.read_csv('data/local/results.csv')
    unique_urls = df['candidate_url'].dropna().unique()
    print(f'Fetching {len(unique_urls)} urls...')
    
    url_to_party = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_party, unique_urls))
        
    for url, party in results:
        url_to_party[url] = party
        
    def get_party(row):
        return url_to_party.get(row['candidate_url'], 'Unknown')
        
    df['party'] = df.apply(get_party, axis=1)
    df.to_csv('data/local/results.csv', index=False)
    print('Fixed CSV!')

if __name__ == '__main__':
    main()
