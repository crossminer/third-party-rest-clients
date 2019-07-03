#!/usr/bin/env python3
# coding: utf8

import requests
import sys
import pprint
import os
import json

projectUrlsToRegister = []
# ALL_PROVIDERS = False

# projectUrlsToRegister = [
#     'https://github.com/ow2-proactive/scheduling', # import
#     'https://github.com/docdoku/docdoku-plm', # import
#     'https://gitlab.ow2.org/asm/asm', # import (sympa missing)
#     'https://gitlab.ow2.org/clif/clif-legacy', # import (sympa missing)
#     'https://gitlab.ow2.org/sat4j/sat4j', # import
#     'https://github.com/bonitasoft/bonita-studio', # create
#     'https://github.com/lutece-platform/lutece-core', # create
#     'https://github.com/xwiki/xwiki-platform', # create
#     'https://github.com/KnowageLabs/Knowage-Server', # create
#     'https://github.com/INRIA/spoon', # import
#     'https://github.com/bonitasoft/bonita-studio', # create
#     'https://github.com/RocketChat/Rocket.Chat', # import
# ]

with open('provision-projects-list.json', 'r') as file:
    projectsMeta = json.load(file)

for p in projectsMeta:
    if p['method'] == 'import':
        if 'url' in p:
            projectUrlsToRegister.append(p['url'])
    elif p['method'] == 'create':
        if 'scavaMeta' in p:
            if 'homePage' in p['scavaMeta']:
                projectUrlsToRegister.append(p['scavaMeta']['homePage'])
    else:
        continue

print(projectUrlsToRegister)

envVariables = {'SCAVA_ADMIN_USERNAME',
                'SCAVA_ADMIN_PASSWORD', 'SCAVA_APIGW_URL', 'GITLAB_TOKEN', 'GITHUB_TOKEN'}
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

# create tokens properties in SCAVA
props = [{"key": "gitlabToken", "value": os.getenv('GITLAB_TOKEN')}, {
    "key": "githubToken", "value": os.getenv('GITHUB_TOKEN')}]

for prop in props:
    try:
        r = requests.get(
            scavaApiGwUrl + '/administration/platform/properties/{}'.format(prop['key']), json=prop, headers=headers)
        r.raise_for_status()

        if 'key' in r.json():
            # key exists, updating it
            try:
                prop['oldkey'] = prop['key']
                r = requests.put(
                    scavaApiGwUrl + '/administration/platform/properties/update', json=prop, headers=headers)
                r.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print('error at updating token properties : {}'.format(e))

        else:
            # key doesn't exist : creating
            try:
                r = requests.post(
                    scavaApiGwUrl + '/administration/platform/properties/create', json=prop, headers=headers)
                r.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print('error at creating token properties : {}'.format(e))

    except requests.exceptions.HTTPError as e:
        print('error at getting properties : {}'.format(e))

# retrieve all the metricproviders for later use when creating task

try:
    allMetricProvidersIds = []
    r = requests.get(
        scavaApiGwUrl + '/administration/analysis/metricproviders', headers=headers)
    r.raise_for_status()
    for metricProvider in r.json():
        # print(metricProvider['metricProviderId'])
        allMetricProvidersIds.append(metricProvider['metricProviderId'])

except requests.exceptions.HTTPError as e:
    print('error at retrieving metricproviders : {}'.format(e))


pScenarioMetricProvidersIds = ['org.eclipse.scava.metricprovider.historic.bugs.users.UsersHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.responsetime.ResponseTimeHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.sentiment.SentimentHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.opentime.OpenTimeHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.emotions.EmotionsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.unansweredbugs.UnansweredThreadsHistoricMetricProvider',
                               'rascal.generic.churn.commitsToday.historic',
                               'trans.rascal.OO.java.DIT-Java-Quartiles.historic',
                               'trans.rascal.OO.java.LCC-Java-Quartiles.historic',
                               'trans.rascal.OO.java.LCOM4-Java-Quartiles.historic',
                               'trans.rascal.LOC.genericLOCoverFiles.historic',
                               'trans.rascal.OO.java.MHF-Java.historic',
                               'trans.rascal.OO.java.PF-Java.historic',
                               'trans.rascal.OO.java.TCC-Java-Quartiles.historic',
                               'rascal.testability.java.TestCoverage.historic']


def getProjects():
    try:
        scavaRegisteredProjects = requests.get(
            scavaApiGwUrl + '/administration/projects', headers=headers)
        scavaRegisteredProjects.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('error at retrieving registered projects : {}'.format(e))
    else:
        return scavaRegisteredProjects.json()


scavaRegisteredProjects = getProjects()


# remove already registered projects URLs from the list
for registered in scavaRegisteredProjects:
    if 'html_url' in registered:
        purl = registered['html_url']
    elif 'homePage' in registered:
        purl = registered['homePage']

    if purl in projectUrlsToRegister:
        print("already registered, removing from list : {}".format(purl))
        projectUrlsToRegister.remove(purl)
    else:
        print("NOT in projectUrlsToRegister: {}".format(purl))


# import projects

for p in projectsMeta:
    if 'url' in p:
        projectUrl = p['url']
    elif 'scavaMeta' in p:
        if 'homePage' in p['scavaMeta']:
            projectUrl = p['scavaMeta']['homePage']
    else:
        projectUrl = None
    if projectUrl in projectUrlsToRegister and projectUrl:
        if p['method'] == 'import':
            try:
                print('projectUrl:{}'.format(projectUrl))
                r = requests.post(scavaApiGwUrl + '/administration/projects/import',
                                  json={'url': projectUrl}, headers=headers)
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print('error at importing the project {} with message {}'.format(r, e))
        elif p['method'] == 'create':
            # create
            try:
                print('projectUrl:{}'.format(projectUrl))
                r = requests.post(scavaApiGwUrl + '/administration/projects/create',
                                  json=p['scavaMeta'], headers=headers)
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(
                    'error at creating the project {} with message {}'.format(r.text, e))
        else:
            sys.exit()

# sys.exit()

# retrieve all projects again to extract their IDs (name)
scavaRegisteredProjects = getProjects()
# print(scavaRegisteredProjects)

# create tasks

for project in scavaRegisteredProjects:
    # print(project['homePage'])
    if('html_url' in project and project['html_url'] in projectUrlsToRegister):
        pShortName = project['shortName']
    elif('homePage' in project and project['homePage'] in projectUrlsToRegister):
        pShortName = project['shortName']
    else:
        print("here")
        sys.exit()

    tasks = {'projectScenario': pScenarioMetricProvidersIds,
             'userScenario': allMetricProvidersIds}
    for task, metricProvidersIds in tasks.items():
        print('will create task {} for project {}'.format(
            task, project['shortName']))
        json = {"analysisTaskId": project['shortName'] + ":" + task, "label": task, "type": "SINGLE_EXECUTION",
                "startDate": "01/01/2018", "endDate": "31/12/2018", "projectId": pShortName, "metricProviders": metricProvidersIds}
        # print(json)
        try:
            r = requests.post(scavaApiGwUrl + '/administration/analysis/task/create',
                              json=json,
                              headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print('error at creating task for the project {} with message {}'.format(
                project['shortName'], e))
