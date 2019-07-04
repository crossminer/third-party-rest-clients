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
