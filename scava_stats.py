#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Get metrics from Scava and publish them in Elasticsearch
# If the collection is a OSSMeter one add project and other fields to items
#
# Copyright (C) 2018 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Valerio Cosentino <valcos@bitergia.com>
#

import argparse
import csv
import logging
import os
import sys
import urllib3

from elasticsearch import Elasticsearch, RequestsHttpConnection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HTTPS_CHECK_CERT = False
FROM_DATE = '1970-01-01'
TO_DATE = '2100-01-01'
NULL_VALUE = 'NaN'

CALCULATION_MIN = 'min'
CALCULATION_MAX = 'max'
CALCULATION_AVG = 'avg'
CALCULATION_SUM = 'sum'
CALCULATION_MEDIAN = 'median'
CALCULATION_LAST = 'last'


def get_params():
    # Mandatory params
    parser = argparse.ArgumentParser(usage="usage: scava_stats [options]", description="Get stats about SCAVA metrics")
    parser.add_argument("-u", "--url", default='http://localhost:8182', help="URL for Scava API REST (default: http://localhost:8182)")
    parser.add_argument("-i", "--index", default='scava-metrics', help="ElasticSearch index in which to import the metrics")
    parser.add_argument("-m", "--metrics", nargs='+', help="List of metrics IDs")
    parser.add_argument("-o", "--output-path", help="Output file path (CSV)")

    # Optional params
    parser.add_argument("--from-date", default="1970-01-01", help="Set from date (default: 1970-01-01)")
    parser.add_argument("--to-date", default="2100-01-01", help="Set to date (default: 2100-01-01)")
    parser.add_argument('-g', '--debug', dest='debug', action='store_true')
    args = parser.parse_args()

    return args


def get_projects(es, index):
    """Get the projects that exist in the `index` of the `es` database.

    :param es: Elasticsearch object
    :param index: Index name
    """
    projects = []

    page = es.search(
        index=index,
        scroll="1m",
        size=10,
        body={
            "size": 0,
            "aggs": {
                "unique_projects": {
                    "terms": {
                        "field": "project",
                        "size": 5000
                    }
                }
            }
        }
    )

    buckets = page['aggregations']['unique_projects']['buckets']

    for bucket in buckets:
        projects.append(bucket['key'])

    return projects


def get_metric_value(es, index, project, metric, calculation_type, from_date=FROM_DATE, to_date=TO_DATE):
    """Get the value for `metric` for `project` based on the data in `index` within the `es` database. The
    value is assessed based on the `calculation_type` which can be [min, max, avg, sum, median, last].
    Optionally, the value can be calculated between a `from_date` and `to_date`.

    :param es: Elasticsearch object
    :param index: Index name
    :param project: Project name
    :param project: Index name
    :param metric: Metric ID
    :param calculation_type: Calculation types covered: [min, max, avg, sum, median, last]
    :param from_date: Start date
    :param to_date: End date
    """
    query = {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {
                        "term": {
                            "project": project
                        }
                    },
                    {
                        "term": {
                            "metric_id": metric
                        }
                    },
                    {
                        "range": {
                            "datetime": {
                                "gte": from_date,
                                "format": "yyyy-MM-dd"
                            }
                        }
                    },
                    {
                        "range": {
                            "datetime": {
                                "lte": to_date,
                                "format": "yyyy-MM-dd"
                            }
                        }
                    }
                ]
            }
        }
    }

    if calculation_type == CALCULATION_LAST:
        aggs = {
            "stat": {
                "top_hits": {
                    "docvalue_fields": [
                        "metric_es_value"
                    ],
                    "_source": "metric_es_value",
                    "size": 1,
                    "sort": [
                        {
                            "datetime": {
                                "order": "desc"
                            }
                        }
                    ]
                }
            }
        }
    elif calculation_type == CALCULATION_MEDIAN:
        aggs = {
            "stat": {
                "percentiles": {
                    "field": "metric_es_value",
                    "percents": [50]
                }
            }
        }
    else:
        aggs = {
            "stat": {
                calculation_type: {
                    "field": "metric_es_value"
                }
            }
        }

    query['aggs'] = aggs

    try:
        page = es.search(
            index=index,
            scroll="1m",
            size=10,
            body=query
        )

        stat = page['aggregations']['stat']

        if 'values' in stat:
            value = stat['values']['50.0']
        elif 'hits' in stat and stat['hits']['total'] > 0:
            value = stat['hits']['hits'][0]['fields']['metric_es_value'][0]
        else:
            value = stat['value']

        if value is None or value == 'NaN':
            value = NULL_VALUE
        else:
            value = "{:.2f}".format(float(value))
    except:
        msg = "No results found for query {}, set value to {}".format(query, NULL_VALUE)
        logging.error(msg)
        value = NULL_VALUE

    return value


def main():
    """The script generates a list of stats (i.e., min, max, avg, sum, median, last) for a set of
    metrics per project, and save the data obtained to an CSV file. Optionally, the stats can be
    calculated in a time range (the default time range is 1970-01-01, 2100-01-01.

    The script can be launched as follows:
        scava_stats
            -u https://admin:admin@localhost:9200
            -i scava-metrics
            -m bugs.inactiveusers bugs.activeusers
            -o /tmp/test.csv
            --from-date 1970-01-01
            --to-date 2010-01-01

    The script requires elasticsearch==6.3.1
    """
    ARGS = get_params()

    url = ARGS.url
    index = ARGS.index
    metrics = ARGS.metrics
    from_date = ARGS.from_date
    to_date = ARGS.to_date
    output_path = ARGS.output_path

    es = Elasticsearch([url], timeout=120, max_retries=20, retry_on_timeout=True,
                       verify_certs=HTTPS_CHECK_CERT, connection_class=RequestsHttpConnection)

    if not es.indices.exists(index=index):
        msg = "Index {} not found!".format(index)
        logging.error(msg)
        sys.exit(-1)

    msg = "Retrieving projects from {} {}".format(url, index)
    logging.debug(msg)
    projects = get_projects(es, index)

    with open(output_path, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        # write headers
        writer.writerow(["Project", "Metric ID", "Max", "Min", "Avg", "Sum", "Median", "Last"])

        for p in projects:
            msg = "Processing project {}".format(p)
            logging.debug(msg)

            for m in metrics:
                metric_max = get_metric_value(es, index, p, m, CALCULATION_MAX, from_date, to_date)
                metric_min = get_metric_value(es, index, p, m, CALCULATION_MIN, from_date, to_date)
                metric_avg = get_metric_value(es, index, p, m, CALCULATION_AVG, from_date, to_date)
                metric_sum = get_metric_value(es, index, p, m, CALCULATION_SUM, from_date, to_date)
                metric_median = get_metric_value(es, index, p, m, CALCULATION_MEDIAN, from_date, to_date)
                metric_last = get_metric_value(es, index, p, m, CALCULATION_LAST, from_date, to_date)

                row = [p, m, metric_max, metric_min, metric_avg, metric_sum, metric_median, metric_last]
                writer.writerow(row)

    msg = "Done! Stats written to {}".format(output_path)
    logging.info(msg)


if __name__ == '__main__':
    main()
