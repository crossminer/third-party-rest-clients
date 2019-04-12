#!/usr/bin/env python3
# coding: utf8

import csv
import requests
import sys
import pprint
import os

envVariables = {'SCAVA_ADMIN_USERNAME',
                'SCAVA_ADMIN_PASSWORD', 'SCAVA_APIGW_URL'}
if not envVariables <= set(os.environ.keys()):
    print('missing environment variable(s). Expected vars: {}'.format(envVariables))
    sys.exit()

# projectsWhitelist = [ 'xwikiwj', 'TestAdrian' ]
<<<<<<< HEAD
projectsWhitelist = ['xwiki']
=======
projectsWhitelist = []
>>>>>>> e8995c7d6c12b9ad10d77b95a4f5916a5a9c0ac2

scavaApiGwUrl = os.getenv('SCAVA_APIGW_URL').strip('/')

headers = {'Content-Type': 'application/json'}
try:
    r = requests.post(scavaApiGwUrl + '/api/authentication', json={'username': os.getenv(
        'SCAVA_ADMIN_USERNAME'), 'password': os.getenv('SCAVA_ADMIN_PASSWORD')}, headers=headers)
    r.raise_for_status()
    headers = {'Authorization': r.headers['Authorization']}
except requests.exceptions.HTTPError as e:
    print('error at authentication : {}'.format(e))


# example metric
# {
#   "id": "bugs.averageSentiment",
#   "name": "Average Sentiment",
#   "description": "The average sentiment per bug repository up to and including the processing date.",
#   "type": "LineChart",
#   "datatable": [
#     {
#       "Date": "20190102",
#       "Average Sentiment": 0
#     },
#     {
#       "Date": "20190105",
#       "Average Sentiment": 0
#     },
#     {
#       "Date": "20190106",
#       "Average Sentiment": 0
#     },
#     {
#       "Date": "20190112",
#       "Average Sentiment": 0
#     },

try:
    r = requests.get(
        scavaApiGwUrl + '/administration/projects', headers=headers)
    r.raise_for_status()
    projectKeys = []

except requests.exceptions.HTTPError as e:
    print('error at retrieving projects : {}'.format(e))

for m in r.json():
    projectKeys.append(m['shortName'])

try:
    r = requests.get(
        scavaApiGwUrl + '/administration/metrics', headers=headers)
    r.raise_for_status()
    metricIds = []

<<<<<<< HEAD
except requests.exceptions.HTTPError as e:
    print('error at retrieving metrics list: {}'.format(e))

for m in r.json():
    metricIds.append(m['id'])

for projectKey in projectKeys:
    if not projectsWhitelist or projectKey in projectsWhitelist:
        print("## projectKey {}".format(projectKey))
        hasValueCount = 0
        rowsWOValue = []
        rowsWValue = []
        header = ['metricId', 'datatable']
        for metricId in metricIds:
            try:
=======
    for m in r.json():
        metricIds.append(m['id'])

    for projectKey in projectKeys:
        if not projectsWhitelist or projectKey in projectsWhitelist:
            print("## projectKey {}".format(projectKey))
            hasValueCount = 0
            metricIdsWValues = []
            metricIdsWOValues = []
            for metricId in metricIds:
>>>>>>> e8995c7d6c12b9ad10d77b95a4f5916a5a9c0ac2
                r = requests.get(
                    scavaApiGwUrl + '/administration/projects/p/{}/m/{}'.format(projectKey, metricId), headers=headers)
                r.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print('error at retrieving metric value : {}'.format(e))
                continue

            r = r.json()
            if len(r['datatable']) > 0:
                hasValueCount += 1
                rowsWValue.append([metricId ,str(r['datatable'])])
            else:
                rowsWOValue.append([metricId , 'empty datatable'])

        print("project has {} metrics with datatable values".format(hasValueCount))
        # print(rowsWValue)

        #

        with open('metricsvalues/{}-metrics-values.csv'.format(projectKey), 'w', newline='') as file:
            writer = csv.writer(file)
            rowsWValue.sort()
            rowsWOValue.sort()
            writer.writerows(rowsWValue)
            writer.writerows(rowsWOValue)
        # print("metrics with datatable not empty: {}\n".format(metricIdsWValues))
        # print("metrics with empty datatable: {}".format(metricIdsWOValues))
