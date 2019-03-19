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

    for m in r.json():
        projectKeys.append(m['shortName'])

    r = requests.get(
        scavaApiGwUrl + '/administration/metrics', headers=headers)
    r.raise_for_status()
    metricIds = []

    for m in r.json():
        metricIds.append(m['id'])

    for projectKey in projectKeys:
        print("## projectKey {}".format(projectKey))
        hasValueCount = 0
        metricIdsWValues = []
        metricIdsWOValues = []
        for metricId in metricIds:
            r = requests.get(
                scavaApiGwUrl + '/administration/projects/p/{}/m/{}'.format(projectKey, metricId), headers=headers)
            r.raise_for_status()

            r = r.json()
            if len(r['datatable']) > 0:
                hasValueCount += 1
                metricIdsWValues.append(metricId)
            else:
                metricIdsWOValues.append(metricId)

        print("project has {} metrics with datatable values".format(hasValueCount))
        print("metrics with datatable not empty: {}".format(metricIdsWValues))
        print("metrics with empty datatable: {}".format(metricIdsWOValues))

            # print("metricId => {}, datatable size => {}".format(metricId, len(r['datatable'])))


except requests.exceptions.HTTPError as e:
    print('error at retrieving metrics : {}'.format(e))
