from api_insee import ApiInsee
from dotenv import load_dotenv
import os
import logging
import sys
import pandas as pd
import csv
import time

load_dotenv()

def getCatNameFromCode(cat_map, code):
    cat_code = code.split('.')[0]
    if not cat_code.isdigit():
        # print(f"code {code} is an invalid code")
        return None
    cat_code = int(cat_code)
    res = cat_map.loc[cat_map['Code'] == cat_code]
    if res.empty:
        # print(f"couldnt find category name for code {code}")
        return None
    return res.iloc[0]['activite']

def getSectionCodes():
    with open('./data/sections.csv') as s:
        reader = csv.DictReader(s, delimiter=';')
        lines = []
        for row in reader:
            lines.append(row)
        sections = []
        for i in range (len(lines)):
            codes = []
            if 'SECTION' in lines[i]['Code']:
                section = [lines[i]['Code'].replace('SECTION ',''),lines[i]['activite']]
                i += 1
                while i < len(lines) and 'SECTION' not in lines[i]['Code']:
                    codes.append(lines[i]['Code'])
                    i+=1
            if codes:
                sections.append([section,codes])

    return sections

def getSectionFromCode(sections, code):
    cat_code = code.split('.')[0]
    for section in sections:
        if cat_code in section[1]:
            return(' '.join(section[0]))
    # print(f"couldnt find section for code {code}")
    return None

def getSiretsFromApi():
    try:
        api = ApiInsee(
            key = os.getenv('consummer_key',''),
            secret = os.getenv('secret_key','')
        )
    except:
        raise KeyError('API Authentification failed, Please verify consumer and secret keys ')

    champs = [
        'siret',
        'siren',
        'activitePrincipaleUniteLegale',
        'codeCommuneEtablissement',
        'etatAdministratifUniteLegale',
        'libelleCommuneEtablissement'
    ]

    request = api.siret(q='etatAdministratifUniteLegale:A', champs=champs)

    etablissements = []

    for (page_index, page_result) in enumerate(request.pages(nombre=1000)):
        for result in page_result['etablissements']:
            etablissements.append({'siret' : result['siret'], 
                                'activitePrincipaleUniteLegale' : result['uniteLegale']['activitePrincipaleUniteLegale'],
                                'codeCommuneEtablissement' : result['adresseEtablissement']['codeCommuneEtablissement'],
                                'etatAdministratifUniteLegale' : result['uniteLegale']['etatAdministratifUniteLegale'],
                                'libelleCommuneEtablissement' : result['adresseEtablissement']['libelleCommuneEtablissement']
                                })
        
        print(f"Page number {str(page_index)}")
        print(f"Fetched {str(len(etablissements))}")
        # if page_index > 0:
        #     break

    df = pd.DataFrame.from_records(etablissements)

    df.to_csv('all_siret.csv', index=False)
    return df

def processSirets(fromAPI = False):
    if fromAPI:
        df = getSiretsFromApi()
    else:
        df = pd.read_csv('./results/all_siret.csv')

    section_codes = getSectionCodes()
    cat_map = pd.read_csv('./data/categories.csv', delimiter=';')

    df['section'] = df['activitePrincipaleUniteLegale'].apply(lambda x: getSectionFromCode(section_codes, x))
    df['categories'] = df['activitePrincipaleUniteLegale'].apply(lambda x: getCatNameFromCode(cat_map, x))

    valid_df = df.dropna(subset=['section', 'categories'], thresh=1).copy()
    unknown = df.loc[~df['siret'].isin(valid_df['siret'])].copy().astype({'siret': 'str'})

    et_by_city_section = valid_df.groupby(['codeCommuneEtablissement','libelleCommuneEtablissement','section'])

    et_by_city_section_nb = et_by_city_section.size().reset_index(name='nb')

    et_by_city_category = valid_df.groupby(['codeCommuneEtablissement','libelleCommuneEtablissement','categories'])

    et_by_city_category_nb = et_by_city_category.size().reset_index(name='nb')

    print(et_by_city_section_nb)
    print(et_by_city_category_nb)
    # print(et_by_city_section_nb.sort_values('libelleCommuneEtablissement'))
    # print(et_by_city_category_nb.sort_values('libelleCommuneEtablissement'))

    et_by_city_section_nb.to_csv('./results/et_by_city_section_nb.csv', index=False)
    et_by_city_category_nb.to_csv('./results/et_by_city_category_nb.csv', index=False)
    unknown.to_csv('./results/unknown.csv', index=False)


    with pd.ExcelWriter('./results/result.xlsx') as writer:
        et_by_city_section_nb.to_excel(writer, sheet_name = 'Nb par Section', index=False)
        et_by_city_category_nb.to_excel(writer, sheet_name = 'Nb par Categorie', index=False)
        unknown.to_excel(writer, sheet_name = 'Code inconnu', index=False)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        processSirets()
    else:
        if sys.argv[1] != 'api':
            raise TypeError("Provide 'api' argument to fetch data from the Sirene API")
        processSirets(True)