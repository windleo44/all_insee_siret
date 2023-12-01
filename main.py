from api_insee import ApiInsee
from dotenv import load_dotenv
import os
import logging
import sys
import pandas as pd

load_dotenv()

def getActNameFromCode(act_map, code):
    res = act_map.loc[act_map['Code'] == code]
    if res.empty:
        # print(f"couldnt find activity name for code {code}")
        return code
    return res.iloc[0]['activite']

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
    if page_index > 100:
        break

df = pd.DataFrame.from_records(etablissements)

df.to_csv('all_siret.csv', index=False)

act_map = pd.read_excel('act_mapping.xls')

grouped_city = df.groupby(['libelleCommuneEtablissement','activitePrincipaleUniteLegale'])

et_by_city_activities = grouped_city.size().reset_index(name='nb')

et_by_city_activities['Nom activite'] = et_by_city_activities['activitePrincipaleUniteLegale'].apply(lambda x: getActNameFromCode(act_map, x))

print(et_by_city_activities)

et_by_city_activities[['libelleCommuneEtablissement','activitePrincipaleUniteLegale','Nom activite','nb']].to_excel('result.xlsx', index=False)
