![screenshot](https://raw.githubusercontent.com/ChrisYounger/get_itsi_thresholds/master/appserver/static/demo.png)

# Get ITSI Thresholds - custom command

A custom command that will retrieve the values of the time-based ITSI thresholds that are set for a KPI. Works with static ITSI thresholds or Adaptive thresholds.

`| getitsithresholds service=<serviceid-string> kpi=<kpi-string> mode=(normal|raw|columns)`

This can be used as a generating command or a steaming command. If used as a streaming command, it must have a `_time` column. It will use this `_time` column to match the thresholds with the correct data rows. Data can be supplied in any granularity however if the time block extends through multiple time policies, then only the first time policy will be output. For this reason, its best to use data with hourly granularity or smaller. 


Simple example to retrieve thresholds (generating command):

    | getitsithresholds service=c2d8f443-fd65-4872-b3b8-1ac7757b57f6 kpi=a672f70631ce28a0be31e1f2`


Example merging with data (streaming command):

    index="itsi_summary" itsi_service_id=c2d8f443-fd65-4872-b3b8-1ac7757b57f6 kpiid=a672f70631ce28a0be31e1f2 
    | timechart span=1h avg(alert_value) as alert_value
    | getitsithresholds service=c2d8f443-fd65-4872-b3b8-1ac7757b57f6 kpi=a672f70631ce28a0be31e1f2


Modes: 
* mode=`normal` (default) - will output a single field `regions` containing the severity name, the colour and the threshold value.
* mode=`raw` - will output an unmodified JSON structure for each time policy
* mode=`columns` - will output data as individual fields (`hour`, `policy`, `min`, `max`, `severityX`..., `colorX`..., `thresholdX`...). ITSI can be configured with different amounts of severities for each time policy, this is why the columns are output like this.


Output from this command (using mode=normal) can be charted using the "Region Chart Visualization" here: https://splunkbase.splunk.com/app/4911/


Copyright (C) 2020 Chris Younger. I am a Splunk Professional Services consultant working for JDS Australia, in Brisbane Australia.

[Splunkbase](https://splunkbase.splunk.com/app/4910/#/details) | [Source code](https://github.com/ChrisYounger/get_itsi_thresholds) | [Questions, Bugs or Suggestions](https://answers.splunk.com/app/questions/4910.html) | [My Splunk apps](https://splunkbase.splunk.com/apps/#/author/chrisyoungerjds)