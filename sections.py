import csv, sys, json
import pandas as pd


# with open('sections.csv') as s:
#     reader = csv.DictReader(s, delimiter=';')
#     lines = []
#     for row in reader:
#         lines.append(row)
#     sections = []
#     for i in range (len(lines)):
#         codes = []
#         if 'SECTION' in lines[i]['Code']:
#             section = [lines[i]['Code'],lines[i]['activite']]
#             i += 1
#             while i < len(lines) and 'SECTION' not in lines[i]['Code']:
#                 codes.append(lines[i]['Code'])
#                 i+=1
#         if codes:
#             sections.append([section,codes])
# code = '10.6'
# for section in sections:
#     if code in section[1]:
#         print(section[0])

with open('sections.csv') as s, open('categories.csv', 'w') as c:
    reader = csv.DictReader(s, delimiter=';')
    writer = csv.DictWriter(c, fieldnames=['Code','activite'], delimiter=';')
    writer.writeheader()
    for row in reader:
        if '.' not in row['Code'] and 'SECTION' not in row['Code']:
            writer.writerow(row)
