#!/usr/bin/env python3
# coding: utf8

import requests
import sys
import pprint
import os

projectUrlsToRegister = [
        'https://github.com/xwiki/xwiki-platform',
#        'https://github.com/imixs/imixs-workflow',
        'https://github.com/KnowageLabs/Knowage-Server',
#        'https://github.com/RocketChat/Rocket.Chat',
#        'https://github.com/INRIA/spoon',
#        'https://github.com/bonitasoft/bonita-studio',
        ]


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

try:
    metricProvidersIds  = []
    r = requests.get(scavaApiGwUrl + '/administration/analysis/metricproviders', headers=headers)
    r.raise_for_status()
    for metricProvider in r.json():
        # print(metricProvider['metricProviderId'])
        metricProvidersIds.append(metricProvider['metricProviderId'])

except requests.exceptions.HTTPError as e:
    print('error at retrieving metricproviders : {}'.format(e))


def getProjects():
    try:
        scavaRegisteredProjects = requests.get(scavaApiGwUrl + '/administration/projects', headers=headers)
        scavaRegisteredProjects.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('error at retrieving registered projects : {}'.format(e))
    else:
        return scavaRegisteredProjects.json()


scavaRegisteredProjects = getProjects()


# remove already registered projects URLs from the list
for registered in scavaRegisteredProjects:
    if 'html_url' in registered:
        if registered['html_url'] in projectUrlsToRegister:
            print("already registered : {}".format(registered['html_url']))
            projectUrlsToRegister.remove(registered['html_url'])
        else:
            print("NOT in projectUrlsToRegister: {}".format(registered['html_url']))


for projectUrl in projectUrlsToRegister:
    try:
        print('projectUrl:{}'.format(projectUrl))
        r = requests.post(scavaApiGwUrl + '/administration/projects/import', json = {'url' : projectUrl}, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('error at importing the project {} with message {}'.format(r,e))

# retrieve all projects again to extract their IDs (name)
scavaRegisteredProjects = getProjects()

for project in scavaRegisteredProjects:
    if('html_url' in project and project['html_url'] in projectUrlsToRegister):
            print('will create task for: ' + project['shortName'])
            json = {"analysisTaskId":project['shortName'] + ":task","label":"task","type":"SINGLE_EXECUTION","startDate":"02/01/2019","endDate":"04/01/2019","projectId":project['shortName'],"metricProviders":metricProvidersIds}
            # print(json)
            try:
                r = requests.post(scavaApiGwUrl + '/administration/analysis/task/create',
                json = json,
                headers=headers)
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print('error at creating task for the project {} with message {}'.format(project['shortName'],e))
