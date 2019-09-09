#!/usr/bin/env python3
# coding: utf8

from datetime import datetime,timedelta
import csv
import requests
import sys
import pprint
import statistics
import os

envVariables = {'SCAVA_ADMIN_USERNAME',
                'SCAVA_ADMIN_PASSWORD', 'SCAVA_APIGW_URL'}
if not envVariables <= set(os.environ.keys()):
    print('missing environment variable(s). Expected vars: {}'.format(envVariables))
    sys.exit()

# projectsWhitelist = [ 'xwikiwj', 'TestAdrian' ]
projectsWhitelist = []
# projectsWhitelist = ['xwiki', 'spoon']

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
else:
    for m in r.json():
        projectKeys.append(m['shortName'])

try:
    r = requests.get(
        scavaApiGwUrl + '/administration/metrics', headers=headers)
    r.raise_for_status()
except requests.exceptions.HTTPError as e:
    print('error at retrieving metrics list: {}'.format(e))
else:
    metricIds = []

for m in r.json():
    metricIds.append(m['id'])
    # https://github.com/crossminer/scava/issues/219
    # hasDate = False
    # for col in m['datatable']['cols']:
    #     if col['name'] == 'Date':
    #         hasDate = True
    #         break
    # if not hasDate:
    #     print("no column 'Date' in {} (metridId: {})".format(m['id'], m['metricId']))


  # "datatable": [
  #   {
  #     "Date": "20180101",
  #     "Comments": 0,
  #     "Requests": 0,
  #     "Replies": 0
  #   },
  #   {
  #     "Date": "20180102",
  #     "Comments": 0,
  #     "Requests": 0,
  #     "Replies": 0
  #   },
  #   {

def create_item_metrics_from_barchart(mdata):
    if not isinstance(mdata['y'], str):
        logging.debug("Barchart metric, Y axis not handled %s", mdata)
        return []

    values = [bar[mdata['y']] for bar in mdata['datatable']]

    max_values = max(values)
    min_values = min(values)
    mean_values = statistics.mean(values)
    median_values = statistics.median(values)

    metric_max = {
        'metric_class': mdata['id'].split(".")[0],
        'metric_type': mdata['type'],
        'metric_id': mdata['id'] + '_max',
        'metric_desc': mdata['description'] + '(Max)',
        'metric_name': mdata['name'] + '(Max)',
        'metric_es_value': max_values,
        'metric_es_compute': 'sample',
        'datetime': mupdated,
        'scava': mdata
    }

    metric_min = {
        'metric_class': mdata['id'].split(".")[0],
        'metric_type': mdata['type'],
        'metric_id': mdata['id'] + '_min',
        'metric_desc': mdata['description'] + '(Min)',
        'metric_name': mdata['name'] + '(Min)',
        'metric_es_value': min_values,
        'metric_es_compute': 'sample',
        'datetime': mupdated,
        'scava': mdata
    }

    metric_mean = {
        'metric_class': mdata['id'].split(".")[0],
        'metric_type': mdata['type'],
        'metric_id': mdata['id'] + '_mean',
        'metric_desc': mdata['description'] + '(Mean)',
        'metric_name': mdata['name'] + '(Mean)',
        'metric_es_value': mean_values,
        'metric_es_compute': 'sample',
        'scava': mdata
    }

    metric_median = {
        'metric_class': mdata['id'].split(".")[0],
        'metric_type': mdata['type'],
        'metric_id': mdata['id'] + '_median',
        'metric_desc': mdata['description'] + '(Median)',
        'metric_name': mdata['name'] + '(Median)',
        'metric_es_value': median_values,
        'metric_es_compute': 'sample',
        'scava': mdata
    }

    return [metric_max, metric_min, metric_mean, metric_median]


def create_item_metrics_from_linechart(mdata):
    metrics = []
    if isinstance(mdata['y'], str):
        metric = {}
        for sample in mdata['datatable']:
            metric['metric_class'] = mdata['id'].split(".")[0]
            metric['metric_type'] = mdata['type']
            metric['metric_id'] = mdata['id']
            metric['metric_desc'] = mdata['description']
            metric['metric_name'] = mdata['name']
            metric['metric_es_compute'] = 'cumulative'
            metric['scava'] = mdata
            metric['metric_es_value'] = None

            if 'y' in mdata and mdata['y'] in sample:
                metric['metric_es_value'] = sample[mdata['y']]
            elif 'Smells' in sample:
                metric['metric_es_value'] = sample['Smells']

            if metric['metric_es_value'] is None:
                logging.debug("Linechart metric not handled %s", sample)

            if 'Date' in sample:
                metric['metric_es_compute'] = 'sample'
                metric['datetime'] = sample['Date']

            metrics.append(metric)
    elif isinstance(mdata['y'], list):
        for sample in mdata['datatable']:
            for y in mdata['y']:
                metric = {
                    'metric_class': mdata['id'].split(".")[0],
                    'metric_type': mdata['type'],
                    'metric_id': mdata['id'] + '_' + y,
                    'metric_desc': mdata['description'] + '(' + y + ')',
                    'metric_name': mdata['name'] + '(' + y + ')',
                    'metric_es_value': sample[y],
                    'metric_es_compute': 'cumulative',
                    'scava': mdata
                }

                if 'Date' in sample:
                    metric['metric_es_compute'] = 'sample'
                    metric['datetime'] = sample['Date']

                metrics.append(metric)
    else:
        logging.debug("Linechart metric, Y axis not handled %s", mdata)

    return metrics


def create_item_metrics_from_linechart_series(mdata):
    metrics = []
    for sample in mdata['datatable']:
        if isinstance(mdata['y'], str):
            metric = {
                'metric_class': mdata['id'].split(".")[0],
                'metric_type': mdata['type'],
                'metric_id': mdata['id'] + '_' + mdata['series'],
                'metric_desc': mdata['description'] + '(' + mdata['series'] + ')',
                'metric_name': mdata['name'] + '(' + mdata['series'] + ')',
                'metric_es_value': sample[mdata['y']],
                'metric_es_compute': 'cumulative',
                'scava': mdata
            }

            if 'Date' in sample:
                metric['metric_es_compute'] = 'sample'
                metric['datetime'] = sample['Date']
            if mdata['series'] in sample:
                metric['metric_id'] = mdata['id'] + '_' + sample[mdata['series']]
                metric['metric_desc'] = mdata['description'] + '(' + sample[mdata['series']] + ')',
                metric['metric_name'] = mdata['name'] + '(' + sample[mdata['series']] + ')'

            metrics.append(metric)
        else:
            logging.debug("Linechart series metric, Y axis not handled %s", mdata)
    return metrics


def extract_metrics(scava_metric):
    """
    Extract metric names and values from an scava_metric. It can be
    a cumulative value or a time series value metric. The time series will
    generate one metric per each sample.

    :param scava_metric: metric collected using Scava API REST
    :return: the list of metrics values from a scava_metric
    """

    mdata = scava_metric
    item_metrics = []

    if not mdata['datatable']:
        item_metric = {
            'metric_type': mdata['type'],
            'metric_id': mdata['id'],
            'metric_desc': mdata['description'],
            'metric_name': mdata['name'],
        }
        item_metrics.append(item_metric)

    elif mdata['type'] == 'BarChart':
        for item_metric in create_item_metrics_from_barchart(mdata):
            item_metrics.append(item_metric)
    elif mdata['type'] == 'LineChart' and 'series' not in mdata:
        for item_metric in create_item_metrics_from_linechart(mdata):
            item_metrics.append(item_metric)
    elif mdata['type'] == 'LineChart':
        for item_metric in create_item_metrics_from_linechart_series(mdata):
            item_metrics.append(item_metric)
    else:
        logging.debug("Metric type %s not handled, skipping item %s", mdata['type'], scava_metric)

    # logging.debug("Metrics found: %s", item_metrics)
    return item_metrics

def genMetricDaysRows(days,mdata):
    """return an array of values, one item per day"""
    # rowvalues = []
    # print(days)
    rows = []
         # if isinstance(mdata['y'], str):
    if mdata['type'] != 'LineChart':
        metricId = mdata['id'] + '_' + mdata['y']
        row = [ metricId ]
        row.append(mdata['datatable'])
        rows.append(row)
        return(rows)
    if isinstance(mdata['y'], list):
        for dimension in mdata['y']:
            metricId = mdata['id'] + '_' + dimension
            row = [ metricId ]
            for day in days:
                # print("for day: {}".format(day))
                day_found = False
                for sample in mdata['datatable']:
                    # print("sample day: {}".format(sample['Date']))
                    if sample['Date'] == day:
                        row.append(sample[dimension])
                        day_found = True
                        break
                if not day_found:
                    row.append("nodata")
            # print("row for {} with len {} is {}".format(metricId,len(row),row))
            rows.append(row)
        return(rows)
    elif isinstance(mdata['y'], str):
        dimensions = []
        dimensions.append(mdata['y'])
        if 'series' in mdata:
            dimensions.append(mdata['series'])
        for dimension in dimensions:
            metricId = mdata['id'] + '_' + dimension
            row = [ metricId ]
            for day in days:
                # print("for day: {}".format(day))
                # day_found = False
                for sample in mdata['datatable']:
                    # at the end of the loop, we'll have a complete line in the CSV
                    # print("sample day: {}".format(sample))
                    if 'Date' in sample and sample['Date'] == day:
                        # day_found = True
                        # if sample['Date'] == curDay:
                        if 'series' in mdata:
                            metricId = mdata['id'] + '_' + dimension + '(' + sample[mdata['series']] + ')'
                            row[0] = metricId
                        if sample['Date'] == "20180525":
                            print("{} sample value : {} -> {}".format(day,metricId,sample))
                            # print([mdata['y'],dimension])
                            # print(list(sample.keys()))
                            # print(all(elem in [mdata['y'], dimension] for elem in list(sample.keys())))
                        # if 'y' in mdata and mdata['y'] in sample and dimension in sample:
                        if 'y' in mdata and all(elem in list(sample.keys()) for elem in [mdata['y'], dimension]):
                            sample_value = sample[dimension]
                        elif 'Smells' in sample:
                            sample_value = sample['Smells']
                        else:
                            sample_value = "noValueForDimension"
                        row.append(sample_value)
                        print(len(row))
                    else:
                        # this sample is not for the current day : next
                        row.append("noValueOrNoDate")
                # print(len(row))
                rows.append(row)
        return(rows)
    else:
        print('type of y not handled')

                # metric = {
                # 'project': mdata['projectId'],
                # 'metric_class': mdata['id'].split(".")[0],
                # 'metric_type': mdata['type'],
                # 'metric_id': mdata['id'] + '_' + y,
                # 'metric_desc': mdata['description'] + '(' + y + ')',
                # 'metric_name': mdata['name'] + '(' + y + ')',
                # 'metric_es_value': sample[y],
                # 'metric_es_compute': 'cumulative',
                # 'datetime': mupdated,
                # 'scava': mdata
                # }

for projectKey in projectKeys:
    if not projectsWhitelist or projectKey in projectsWhitelist:
        print("## projectKey {}".format(projectKey))
        hasValueCount = 0
        rowsWOValue = []
        rowsWValue = []
        days = []
        start,end = datetime(2018, 1, 1), datetime(2018, 12, 31)
        dates = [start + timedelta(days=i) for i in range((end-start).days+1)]
        for dte in dates:
            days.append(dte.strftime('%Y%m%d'))
        # print(days)

        header = ['metricId']
        header.extend(days)
        # print(header)
        # sys.exit()
        for metricId in metricIds:
            if(metricId != "bugs.emotions.commentPercentages"): continue
            # print(metricId)
            try:
                r = requests.get(
                    scavaApiGwUrl + '/administration/projects/p/{}/m/{}'.format(projectKey, metricId), headers=headers)
                r.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print('error at retrieving metric value : {}'.format(e))
                continue

            r = r.json()
            if len(r['datatable']) > 0:
                hasValueCount += 1
                # rows = genMetricDaysRows(days, r)
                rows = extract_metrics(r)
                sys.exit()
                if rows:
                    # print("rows ({}) for this metric are {}".format(len(rows),rows))
                    for row in rows:
                        rowsWValue.append(row)


                # print(r['datatable'])
            else:
                rowsWOValue.append([metricId , 'empty datatable'])

        print("project has {} metrics with datatable values".format(hasValueCount))
        # print(rowsWValue)

        #
        # sys.exit()

        with open('metricsvalues/{}-metrics-values.csv'.format(projectKey), 'w', newline='') as file:
            writer = csv.writer(file)
            rowsWValue.sort()
            rowsWOValue.sort()
            writer.writerow(header)
            writer.writerows(rowsWValue)
            writer.writerows(rowsWOValue)
        # print("metrics with datatable not empty: {}\n".format(metricIdsWValues))
        # print("metrics with empty datatable: {}".format(metricIdsWOValues))
