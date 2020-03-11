![screenshot](https://raw.githubusercontent.com/ChrisYounger/get_itsi_thresholds/master/appserver/static/demo.png)

# Get ITSI Thresholds - custom command

`| getitsithresholds service=<serviceid-string> kpi=<kpi-string> mode=(normal|raw|columns))`

A custom command that will retreive the values of the time-based ITSI thresholds that are set for a KPI. Works with static ITSI thresholds or Adaptive thrseholds.

This can be used as a generating command or a steaming command. If data is passed to the command, it must have a _time column. The command will use this _time column to match the thresholds with the correct rows. Data can be supplied in any granularity however if the time block extends through multiple time policies, then only the first time policy will be set. For this reason, its best to use hourly granularity or smaller. 

Output from this command can be charted using the "Region Chart Visualization" here: https://splunkbase.splunk.com/app/4911/

Modes: 
* mode=normal (default) - will output a single field "regions" containing the severity name, the colour and the threshold value.
* mode=raw - will output an unmodified JSON structure for eadch time policy
* mode=columns - will output data as individual fields (hour, policy, min, max, severityX..., colorX..., thresholdX...). ITSI can be configured with different amounts of severities for each time policy, this is why the columns are output like this.



Copyright (C) 2020 Chris Younger. I am a Splunk Professional Services consultant working for JDS Australia, in Brisbane Australia.

[Splunkbase](https://splunkbase.splunk.com/app/4911/#/details) | [Source code](https://github.com/ChrisYounger/region_chart_viz) | [Questions, Bugs or Suggestions](https://answers.splunk.com/app/questions/4911.html) | [My Splunk apps](https://splunkbase.splunk.com/apps/#/author/chrisyoungerjds)