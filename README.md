![screenshot](https://raw.githubusercontent.com/ChrisYounger/get_itsi_thresholds/master/appserver/static/demo.png)

# Get ITSI Thresholds - custom command

A custom command that will retrieve the values of the time-based ITSI thresholds that are set for a KPI. Works with static ITSI thresholds or adaptive thresholds.

`| getitsithresholds [services=<serviceid-comma-separated-string>] mode=(now|nowextended)`

or 

`| getitsithresholds service=<serviceid-string> kpi=<kpi-string> mode=(normal|raw|columns)`

See the Splunkbase page for more detailed documentation

Output from this command (using mode=normal) can be charted using the "Region Chart Visualization" here: https://splunkbase.splunk.com/app/4911/


Copyright (C) 2020 Chris Younger | [Splunkbase](https://splunkbase.splunk.com/app/4910/#/details) | [Source code](https://github.com/ChrisYounger/get_itsi_thresholds) | [Questions, Bugs or Suggestions](https://answers.splunk.com/app/questions/4910.html) | [My Splunk apps](https://splunkbase.splunk.com/apps/#/author/chrisyoungerjds)