#!/usr/bin/env python3
# coding: utf8

import csv
import requests
import sys
import pprint
import os

envVariables = {'SCAVA_ADMIN_USERNAME', 'SCAVA_ADMIN_PASSWORD', 'SCAVA_APIGW_URL'}
if not envVariables <= set(os.environ.keys()):
    print('missing environment variable(s). Expected vars: {}'.format(envVariables))
    sys.exit()

scavaApiGwUrl = os.getenv('SCAVA_APIGW_URL').strip('/')

headers = {'Content-Type' : 'application/json'}
try:
    r = requests.post(scavaApiGwUrl + '/api/authentication', json = {'username': os.getenv('SCAVA_ADMIN_USERNAME'), 'password': os.getenv('SCAVA_ADMIN_PASSWORD')}, headers=headers)
    r.raise_for_status()
    headers = {'Authorization' : r.headers['Authorization']}
except requests.exceptions.HTTPError as e:
    print('error at authentication : {}'.format(e))


# example metric
  # {
  #   "id": "bugs.requestsreplies-useraverage",
  #   "name": "Comments, Requests and Replies Per User",
  #   "description": "The average number of comments, requests and replies per user, up to and including the current date.",
  #   "type": "LineChart",
  #   "datatable": {
  #     "cols": [
  #       {
  #         "name": "Date",
  #         "field": "$__date"
  #       },
  #       {
  #         "name": "Comments",
  #         "field": "$averageCommentsPerUser"
  #       },
  #       {
  #         "name": "Requests",
  #         "field": "$averageRequestsPerUser"
  #       },
  #       {
  #         "name": "Replies",
  #         "field": "$averageRepliesPerUser"
  #       }
  #     ]
  #   },
  #   "x": "Date",
  #   "y": [
  #     "Comments",
  #     "Requests",
  #     "Replies"
  #   ],
  #   "timeSeries": true
  # },

# processing metrics

try:
    r = requests.get(scavaApiGwUrl + '/administration/metrics', headers=headers)
    r.raise_for_status()
    metrics = []
    row = []
    metrics.append(["id", "providerid", "name", "description", "x","y", "name", "field", "name", "field", "name", "field", "name", "field"])

    for m in r.json():
        row = [m['id'], m['metricId'], m['name'], m['description']]
        row.extend([m['x'],m['y']])
        for e in (m['datatable']['cols']):
            row.extend([e['name'],e['field']])
        metrics.append(row)

except requests.exceptions.HTTPError as e:
    print('error at retrieving metrics : {}'.format(e))

with open('metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(metrics)

# now procesing factoids

try:
    r = requests.get(scavaApiGwUrl + '/administration/factoids', headers=headers)
    r.raise_for_status()
    factoids = []
    row = []
    factoids.append(["id", "name", "summary", "dependencies"])

    for f in r.json():
        # r = requests.get(scavaApiGwUrl + '/administration/projects/p/xwikiplatform/f/{}'.format(f['id']), headers=headers)
        # r.raise_for_status()
        # fval = r.

        row = [f['id'], f['name'], f['summary'], f['dependencies']]
        factoids.append(row)

except requests.exceptions.HTTPError as e:
    print('error at retrieving metrics : {}'.format(e))

with open('factoids.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(factoids)
