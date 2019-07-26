# third-party-rest-clients

## provision-project.py

You need to set the following env variables:
- SCAVA_ADMIN_USERNAME
- SCAVA_ADMIN_PASSWORD
- SCAVA_APIGW_URL (ie, http://scava-instance:8086)
- GITHUB_TOKEN (default github token)
- GITLAB_TOKEN (default gitlab token)

The script reads a file `provision-projects-list.json` which contains the list of projects to provision and their respective properties. An example is provided in `provision-projects-list.json.dist`

Notice: WIP. There are still hardcoded value in there:
- the task start/end date
- the script creates two tasks, one with all metrics enabled, the other with a specific list of metrics

## scava_stats.py

The script generates a list of stats (i.e., min, max, avg, sum, median, last) for a set of
metrics per project, and save the data obtained to an CSV file. Optionally, the stats can be
calculated in a time range (the default time range is 1970-01-01, 2100-01-01.

The script can be launched as follows:
```
    scava_stats
        -u https://admin:admin@localhost:9200
        -i scava-metrics
        -m bugs.inactiveusers bugs.activeusers
        -o /tmp/test.csv
        --from-date 1970-01-01
        --to-date 2010-01-01
```

The script requires elasticsearch==6.3.1
