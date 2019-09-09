#!/usr/bin/env python3
# coding: utf8

import requests
import sys
import pprint
import os
import json
# from collections import Counter
pp = pprint.PrettyPrinter()

envVariables = {'SCAVA_ADMIN_USERNAME',
                'SCAVA_ADMIN_PASSWORD', 'SCAVA_APIGW_URL'}
if not envVariables <= set(os.environ.keys()):
    print('missing environment variable(s). Expected vars: {}'.format(envVariables))
    sys.exit()

scavaApiGwUrl = os.getenv('SCAVA_APIGW_URL').strip('/')


# authenticate
headers = {'Content-Type': 'application/json'}
try:
    r = requests.post(scavaApiGwUrl + '/api/authentication', json={'username': os.getenv(
        'SCAVA_ADMIN_USERNAME'), 'password': os.getenv('SCAVA_ADMIN_PASSWORD')}, headers=headers)
    r.raise_for_status()
    headers = {'Authorization': r.headers['Authorization']}
except requests.exceptions.HTTPError as e:
    print('error at authentication : {}'.format(e))


# retrieve all the metricproviders for later use when creating task

try:
    allMetricProvidersIds = []
    r = requests.get(
        scavaApiGwUrl + '/administration/analysis/metricproviders', headers=headers)
    r.raise_for_status()
    providersData = r.json()
    for metricProvider in providersData:
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
                               #'trans.rascal.OO.java.TCC-Java-Quartiles.historic',
                               'rascal.testability.java.TestCoverage.historic']

uScenarioMetricProvidersIds = ['org.eclipse.scava.metricprovider.indexing.commits.CommitsIndexingMetricProvider',
                               'org.eclipse.scava.metricprovider.indexing.bugs.BugsIndexingMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.bugs.BugsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.comments.CommentsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.requestsreplies.average.RequestsRepliesHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.newbugs.NewBugsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.newusers.NewUsersHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.patches.PatchesHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.requestsreplies.RequestsRepliesHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.status.StatusHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.severity.SeverityHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.severityresponsetime.SeverityResponseTimeHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.severitysentiment.SeveritySentimentHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.severitybugstatus.SeverityBugStatusHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.topics.TopicsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.unansweredbugs.UnansweredThreadsHistoricMetricProvider',
                               'org.eclipse.scava.metricprovider.historic.bugs.users.UsersHistoricMetricProvider',
                               'rascal.generic.churn.churnPerCommitInTwoWeeks.historic',
                               'rascal.generic.churn.churnPerCommitter.historic',
                               'rascal.generic.churn.churnToday.historic']


# adding providers dependencies for the providers

def getDeps(providersData, providersList):
    deps = []
    for provider in providersData:
        if provider['metricProviderId'] in providersList:
            if len(provider['dependOf']):
                for mp in provider['dependOf']:
                    if mp not in deps:
                        deps.append(mp['metricProviderId'])
            else:
                # no deps for this mp
                continue
    return deps


deps = pScenarioMetricProvidersIds

while len(deps):
    # print("deps before: {}".format(deps))
    deps = getDeps(providersData, deps)
    # print("get deps : {}".format(deps))
    pScenarioMetricProvidersIds.extend(deps)

# removing duplicates
pScenarioMetricProvidersIds = list(set(pScenarioMetricProvidersIds))

# same thing with user scenario providers
deps = uScenarioMetricProvidersIds

while len(deps):
    # print("deps before: {}".format(deps))
    deps = getDeps(providersData, deps)
    # print("get deps : {}".format(deps))
    uScenarioMetricProvidersIds.extend(deps)

# removing duplicates
uScenarioMetricProvidersIds = list(set(uScenarioMetricProvidersIds))


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

# try:
#     r = requests.get(scavaApiGwUrl + '/administration/analysis/task?analysisTaskId=asm:userScenario',
#                      headers=headers)
#     r.raise_for_status()
#     pp.pprint(r.json())
# except requests.exceptions.HTTPError as e:
#     print('error at get task for the project {} with message {}'.format(
#         project['shortName'], e))
#
#
#
# sys.exit()

for project in scavaRegisteredProjects:
    # if project['shortName'] in ['KnowageServer']:
        # tasks = {'userScenarioMin': uScenarioMetricProvidersIds}
        tasks = {'projectScenario': pScenarioMetricProvidersIds}
        for task, metricProvidersIds in tasks.items():

            # # delete task
            # analysisTaskId = project['shortName'] + ":" + task
            # # print(json)
            # moreToDelete = True
            # while moreToDelete:
            #     print('will delete task {} for project {}'.format(
            #     task, project['shortName']))
            #     try:
            #         r = requests.delete(scavaApiGwUrl + '/administration/analysis/task/delete?analysisTaskId=' + analysisTaskId,
            #                             headers=headers)
            #         r.raise_for_status()
            #     except requests.exceptions.HTTPError as e:
            #         moreToDelete = False
            #         print('error at deleting task for the project {} with message {}'.format(
            #             project['shortName'], e))

            # create task
            print('will create task {} for project {}'.format(
                task, project['shortName']))
            json = {"analysisTaskId": project['shortName'] + ":" + task, "label": task, "type": "SINGLE_EXECUTION",
                    "startDate": "01/01/2018", "endDate": "31/12/2018", "projectId": project['shortName'], "metricProviders": metricProvidersIds}
            # print(json)
            try:
                r = requests.post(scavaApiGwUrl + '/administration/analysis/task/create',
                                  json=json,
                                  headers=headers)
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print('error at creating task for the project {} with message {}'.format(
                    project['shortName'], e))
