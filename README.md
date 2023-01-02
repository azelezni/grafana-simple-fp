# Grafana Simple File Provisioning
Grafana-simple-fp is a tool to make managing Grafana alerts as code easier by providing a more readable YAML  
It can be used it either local mode or cluster mode:
* Local mode - reads yaml files and outputs converted yaml to provided path
* Cluster mode - watches for configmaps and creates converted configmaps

## Params
The parameters are supported:

| Name                    | Description                                                                                             | Default | Required |
|-------------------------|---------------------------------------------------------------------------------------------------------|---------|----------|
| `-m` `--mode`           | Specify which mode to run in, either 'cluster' or 'local'                                               | `local` | yes      |
| `-c` `--config`         | Path to config files, supports glob: config/**.yaml                                                     |         | no       |
| `-o` `--out`            | Path to save converted yaml files to                                                                    |         | no       |
| `-l` `--label-selector` | Labels to filter configmaps to read                                                                     |         | no       |
| `-t` `--target-labels`  | Labels to add to created configmaps                                                                     |         | no       |
| `-w` `--watch`          | Enable to run in watch mode, in this mode the program will keep running and watch for configmap changes | `false` | no       |


## Config
Grafana-simple-fp uses the following config format:
```yaml
groups:
    # Group name
  - name: my-awesome-group
    # Folder to place alerts in Grafana UI
    folder: AwesomeGroup
    # Evaluation internal, all alerts in the same group are evaluated with the same interval
    interval: 30s
    rules:
        # Rule name
      - title: my-awesome-rule
        # Labels are used with notification polices to decide who gets notified
        labels:
          opsgenie: my-awesome-group
        # Annotations can be templated with labels returned from query
        annotations:
          description: Pod {{ $labels.pod }} in cluster {{ $labels.cluster }} is down!
          summary: Backend is down!
        # Specify how to handle no-data and execution-error states
        executionState:
          noData: Alerting # NoData|Alerting|OK
          execErr: Error   # Error|Alerting|OK
        # Relative timerange for query, in seconds
        timerange:
          from: 300
          to: 0
        # Query to execute
        query:
          # datasource type
          type: prometheus
          # datasource name
          datasource: prometheus
          # expressions to run
          expression: count by (cluster, pod) (up{cluster="prod1", namespace="default", pod=~"backend-.+"})
        # Alert condition, when this condition is met the alert will fire
        condition:
          # in this case we're alerting if no backend pods are up for 5 minutes
          expression: last() < 1 for(5m)
```

This will be converted to [Grafana file provision](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/#provision-alert-rules) format 
which can be used to manage alert in Grafana

#### Condition Expressions
The expression is made up of a few sections:
```
| reduce-function | threshold | for-duration |
      last()           < 1        for(5m)
```

Examples:
* `last() > 0 for(60s)`
* `last() gt 0 for(60s)`
* `last(dropNN=true) < 0 for(30m)`
* `last(replaceNN=0) lt 0 for(30m)`
* `sum() <> 0:10`
* `sum() in 0:10`
* `mean() >< 0:10 for(1d)`
* `mean() not_in 0:10 for(1d)`


* **reduce-function**: Any alert that returns timeseries must be passed via a reduce function, supported functions are:
  * `min()`
  * `max()`
  * `mean()`
  * `sum()`
  * `count()`
  * `last()`
* **threshold**: Define the threshold of the alert, requires a comparison operator and a value or range:
  * `<` or `lt`
  * `>` or `gt`
  * `<>` or `in`
  * `><` or `not_in`
* **for-duration**: Optional, defines how long the condition must be true until the alert will fire

All reduce functions support non-numeric value handling:
* `dropNN` - drops non-numeric values
* `replaceNN` - replace non-numeric values
