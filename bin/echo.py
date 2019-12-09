from search_command_example_app.search_command import SearchCommand
import splunk.rest
import splunk.search
import json
import pycron
from datetime import datetime, timedelta


class Echo(SearchCommand):
    
    def __init__(self, service=None, kpi=None):
        
        # Save the parameters
        self.service = service
        self.kpi = kpi

        # Initialize the class
        SearchCommand.__init__( self, run_in_preview=True, logger_name='echo_search_command')


    def handle_results(self, results, session_key, in_preview):
        self.logger.warn("Querying thresholds")
        #response, content = splunk.rest.simpleRequest('/services/licenser/groups/Free?output_mode=json', sessionKey=self.session_key)
        #response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service?fields="title,_key,kpis.title,kpis._key,kpis.adaptive_thresholds_is_enabled,kpis.time_variate_thresholds_specification"', sessionKey=self.session_key)
        response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service/' + self.service, sessionKey=self.session_key)
        self.logger.warn("Returned status: " + str(response.status))
        res = []
        if response.status == 200:

            # Parse the JSON content
            #self.logger.warn(content)
            source_datetime = datetime.now()
            startofday = datetime(
                year=source_datetime.year,
                month=source_datetime.month,
                day=source_datetime.day,
                hour=0,
                minute=0,
                second=0
            )
            startofweek = startofday - timedelta(days=startofday.weekday())
            res.append("eod" + str(startofweek))

            contentp = json.loads(content)
            for kpi in contentp["kpis"]:
                self.logger.warn("Found kpi: " + kpi["_key"])
                if kpi["_key"] == self.kpi:
                    self.logger.warn("This is the KPI we need")
                    # dedupAllSeverities = {}
                    # for policy in kpi["time_variate_thresholds_specification"]["policies"]:
                    #     dedupSeverities = {}
                    #     index = 0
                    #     for threshold in kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["thresholdLevels"]:
                    #         if not threshold["severityLabel"] in dedupSeverities:
                    #             dedupSeverities[threshold["severityLabel"]] = 0
                    #         dedupSeverities[threshold["severityLabel"]] += 1
                    #         index += 1
                    #         if not threshold["severityLabel"] in dedupAllSeverities:
                    #             dedupAllSeverities[threshold["severityLabel"]] = 0 
                    #         dedupAllSeverities[threshold["severityLabel"]] = max(index, dedupAllSeverities[threshold["severityLabel"]]
                    #         sorted(d.items(), key=lambda x: x[1]))

                    dpolicy = "UNKNOWN_POLICY"
                    dthreshold = ""
                    dseverity = ""
                    if "default_policy" in kpi["time_variate_thresholds_specification"]["policies"]:
                        dpolicy = "default_policy"
                        dseverity = kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["baseSeverityLabel"]
                        for threshold in kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["thresholdLevels"]:
                            dthreshold += "," + str(threshold["thresholdValue"])
                            dseverity += "," + threshold["severityLabel"]
                    houroffsets = []
                    for i in range(0,168):
                        houroffsets.append(str(i))
                    policies = [dpolicy] * 168
                    thresholds = [dthreshold[1:]] * 168
                    severities = [dseverity] * 168


                    for policy in kpi["time_variate_thresholds_specification"]["policies"]:
                        res.append("Policy:" + policy)
                        res.append("Policy Title:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["title"])
                        res.append("Policy Type:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["policy_type"])
                        res.append("Policy baseSeverityLabel:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"])
                        # dedupSeverities = {}
                        # for threshold in kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["thresholdLevels"]:
                        #     if not threshold["severityLabel"] in dedupSeverities:
                        #         dedupSeverities[threshold["severityLabel"]] = 0
                        #     dedupSeverities[threshold["severityLabel"]] += 1
                        thresStr = ""
                        statusStr = kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"]
                        for threshold in kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["thresholdLevels"]:
                            thresStr += "," + str(threshold["thresholdValue"])
                            statusStr += "," + threshold["severityLabel"]

                        res.append("Threshold: " + thresStr)
                        for timeblock in kpi["time_variate_thresholds_specification"]["policies"][policy]["time_blocks"]:
                            res.append("Timeblock cron:" + str(timeblock[0]))
                            res.append("Timeblock duration:" + str(timeblock[1]))
                            #res.append("Duration:" + str(kpi["time_variate_thresholds_specification"]["policies"][policy]["time_blocks"][0][1]))
                            #res.append(json.dumps(kpi["time_variate_thresholds_specification"]["policies"][policy]["time_blocks"], indent=4, sort_keys=True))
                            hr_offset = 0
                            rem_duration = 0
                            while hr_offset < 168:
                                if rem_duration > 0:
                                    rem_duration -= 1
                                if rem_duration > 0:
                                    res.append("hr offset matches for free:" + str(hr_offset))
                                    # todo check for dupes
                                    #if week_results[hr_offset] is not "":
                                    #    self.logger.error("Found a duplicate block at " + str(hr_offset))
                                    #week_results[hr_offset] = "H" + str(hr_offset) + " " + thresStr
                                    #week_results[hr_offset] = thresStr + "\" " + statusStr + "\""
                                    policies[hr_offset] = policy
                                    thresholds[hr_offset] = thresStr[1:]
                                    severities[hr_offset] = statusStr
                                elif pycron.is_now(timeblock[0], dt=(startofweek + timedelta(hours=hr_offset))):
                                    res.append("hr offset matches:" + str(hr_offset))
                                    #if week_results[hr_offset] is not "":
                                    #    self.logger.error("Found a duplicate block at " + str(hr_offset))
                                    #week_results[hr_offset] = "H" + str(hr_offset) + " " + thresStr
                                   # week_results[hr_offset] = thresStr + "\" " + statusStr + "\""
                                    policies[hr_offset] = policy
                                    thresholds[hr_offset] = thresStr[2:]
                                    severities[hr_offset] = statusStr
                                    rem_duration = timeblock[1] / 60
                                hr_offset += 1



                    res.append(json.dumps(kpi["time_variate_thresholds_specification"]["policies"], indent=4, sort_keys=True))
            #self.logger.warn(json.dumps(contentp, indent=4, sort_keys=True))
        
        #self.output_results([{ 'echo' : res, 'results': week_results}])
        self.output_results([{ 'houroffset': houroffsets, 'policies': policies, 'severities':severities, 'thresholds':thresholds}])
        
if __name__ == '__main__':
    Echo.execute()