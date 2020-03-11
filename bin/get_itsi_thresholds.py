import splunk.rest, splunk.search, json, math, pycron
from get_itsi_thresholds_app.search_command import SearchCommand
from datetime import datetime, timedelta
from collections import OrderedDict

class GetItsiThresholds(SearchCommand):

    def __init__(self, service=None, kpi=None, mode=""):
        # Save the parameters
        self.service = service
        self.kpi = kpi
        self.mode = mode.lower()
        # Initialize the class
        SearchCommand.__init__(self, run_in_preview=False, logger_name='get_itsi_thresholds_command')

    def handle_results(self, results, session_key, in_preview):
        self.logger.info("Querying thresholds for service=\"" + self.service + "\" kpi=\"" + self.kpi + "\" in mode=\"" + self.mode + "\" rows_in=" + str(len(results)) + "")
        #self.logger.info("in_preview=" + str(in_preview))
        #self.logger.info("results=" + str(results))
        houroffsets = []

        # check that the results have a _time field
        if len(results) > 0 and not "_time" in results[0]:
            self.logger.warn("Cannot find the _time column in supplied data.")
            raise Exception("Cannot find the _time column in supplied data.")

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

        try:
            #response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service?fields="title,_key,kpis.title,kpis._key,kpis.adaptive_thresholds_is_enabled,kpis.time_variate_thresholds_specification"', sessionKey=self.session_key)
            response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service/' + self.service, sessionKey=self.session_key)
            #self.logger.info("Returned status: " + str(response.status))
            #self.logger.info("Received response (" + content + ")")
            res = []
            if response.status != 200:
                self.logger.warn("Unexpected service status when retreiving service service configuration (" + self.service + ")")
                raise Exception("Unexpected service status when retreiving service service configuration (" + self.service + ")")
            contentp = json.loads(content)

        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            self.logger.warn("Error retreiving thresholds. Is the service ID correct? [" + message + "]")
            raise Exception("Error retreiving thresholds. Is the service ID correct? [" + message + "]")

        
        for kpi in contentp["kpis"]:
            #self.logger.info("Found kpi: " + kpi["_key"])
            if kpi["_key"] == self.kpi:
                #self.logger.info("This is the KPI we need")
                dpolicy = "UNKNOWN_POLICY"
                dmin = ""
                dmax = ""
                draw = ""
                dthreshold = []
                dseverity = []
                dcolor = []
                if "default_policy" in kpi["time_variate_thresholds_specification"]["policies"]:
                    dpolicy = "default_policy"
                    dseverity.append(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["baseSeverityLabel"])
                    dcolor.append(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["baseSeverityColor"])
                    dmin = kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["renderBoundaryMin"]
                    dmax = kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["renderBoundaryMax"]
                    if self.mode == "raw":
                        draw = json.dumps(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"], indent=4, sort_keys=True)
                    for threshold in kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["thresholdLevels"]:
                        dthreshold.append(str(threshold["thresholdValue"]))
                        dseverity.append(threshold["severityLabel"])
                        dcolor.append(threshold["severityColor"])
                policies = []
                thresholds = []
                severities = []
                colors = []
                rawdata = []
                boundarymin = []
                boundarymax = []
                policytitle = []
                rawdata = []
                for i in range(0,168):
                    houroffsets.append(str(i))
                    policies.append(dpolicy)
                    thresholds.append(dthreshold)
                    severities.append(dseverity)
                    colors.append(dcolor)
                    rawdata.append(draw)
                    boundarymin.append(dmin)
                    boundarymax.append(dmax)
                    policytitle.append("Default")

                for policy in kpi["time_variate_thresholds_specification"]["policies"]:
                    #res.append("Policy:" + policy)
                    #res.append("Policy Title:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["title"])
                    #res.append("Policy Type:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["policy_type"])
                    #res.append("Policy baseSeverityLabel:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"])
                    thresStr = []
                    statusStr = [kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"]]
                    colorStr = [kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityColor"]]
                    for threshold in kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["thresholdLevels"]:
                        thresStr.append(str(threshold["thresholdValue"]))
                        statusStr.append(threshold["severityLabel"])
                        colorStr.append(threshold["severityColor"])

                    res.append("Threshold: " + str(thresStr))
                    for timeblock in kpi["time_variate_thresholds_specification"]["policies"][policy]["time_blocks"]:
                        #res.append("Timeblock cron:" + str(timeblock[0]))
                        #res.append("Timeblock duration:" + str(timeblock[1]))
                        #res.append(json.dumps(kpi["time_variate_thresholds_specification"]["policies"][policy]["time_blocks"], indent=4, sort_keys=True))
                        rraw =  ""
                        if self.mode == "raw":
                            rraw = json.dumps(kpi["time_variate_thresholds_specification"]["policies"][policy], indent=4, sort_keys=True)
                        rem_duration = 0
                        for hr_offset in range(0,168):
                            if rem_duration > 0:
                                rem_duration -= 1
                            if rem_duration > 0 or (pycron.is_now(timeblock[0], dt=(startofweek + timedelta(hours=hr_offset)))):
                                policies[hr_offset] = policy
                                thresholds[hr_offset] = thresStr
                                severities[hr_offset] = statusStr
                                colors[hr_offset] = colorStr
                                boundarymin[hr_offset] = kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["renderBoundaryMin"]
                                boundarymax[hr_offset] = kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["renderBoundaryMax"]
                                policytitle[hr_offset] = kpi["time_variate_thresholds_specification"]["policies"][policy]["title"]
                                rawdata[hr_offset] = rraw
                                if rem_duration < 1:
                                    rem_duration = int(int(timeblock[1]) / 60)

        # if we didnt find 168 time blocks then we could not find the KPi
        if len(houroffsets) != 168:
            self.logger.warn("Unable to find time blocks for KPI. is kpi id correct? Blocks found: " + str(len(houroffsets)))
            raise Exception("Unable to find time blocks for KPI. is kpi id correct? Blocks found: " + str(len(houroffsets)))

        # if no data data supplied, then generate our own
        if len(results) == 0:
            for i in range(0,168):
                results.append(OrderedDict())
        data_hr_offset = -1

        for row in results:
            # if there is no data (user using command as a generating command?) then just increment counter
            if len(row) == 0:
                data_hr_offset += 1
            else:
                # figure out the hour offset for this data row
                data_hr_offset = ((int(row["_time"]) // 3600) + 96) % 168
            # dump the raw json
            if self.mode == "raw":
                row['thresholds'] = rawdata[data_hr_offset]
            # dump each threshold as a column
            elif self.mode == "columns":
                row['hour'] = houroffsets[data_hr_offset]
                row['policy'] = policytitle[data_hr_offset]
                row['min'] = boundarymin[data_hr_offset]
                row['max'] = boundarymax[data_hr_offset]
                for idx, val in enumerate(severities[data_hr_offset]):
                    row['severity' + str(idx)] = val
                for idx, val in enumerate(colors[data_hr_offset]):
                    row['color' + str(idx)] = val
                for idx, val in enumerate(thresholds[data_hr_offset], 1):
                    row['threshold' + str(idx)] = val
            # default mode, output key value pairs in a single string field called "threshold"
            else:
                # could add this commented out code under a mode=="extended" although lets keep it less complicated. if user needs these values then use column mode and they can build it themself.
                # by not including extra information abotu the hour and ppolicy, it means we can better reduce the amount of dom elements on the threshold chart
                #row["thresholds"] = "hour=\"" + str(houroffsets[data_hr_offset])  + "\" policy=\"" + policytitle[data_hr_offset] + "\" min=\"" + str(boundarymin[data_hr_offset]) + "\" max=\"" + str(boundarymax[data_hr_offset]) + "\" severities=\""
                # row["thresholds"] = "severities=\""
                # for idx, val in enumerate(severities[data_hr_offset]):
                #     row["thresholds"] += str(val) + ","
                # row["thresholds"] = row["thresholds"][:-1] + "\" thresholds=\""
                # for idx, val in enumerate(thresholds[data_hr_offset], 1):
                #     row["thresholds"] += str(val) + ","
                # row["thresholds"] = row["thresholds"][:-1] + "\""
                row["regions"] = ""
                for idx, val in enumerate(severities[data_hr_offset]):
                    row["regions"] += str(val) + "=" + str(colors[data_hr_offset][idx]) # + " " + str(idx) + " " + str(len(thresholds[data_hr_offset]))
                    if (idx < len(thresholds[data_hr_offset])):
                        row["regions"] += "," + str(thresholds[data_hr_offset][idx]) + ","

        self.logger.info("Returning " + str(len(results)) + " results")
        # output the data
        self.output_results(results)

if __name__ == '__main__':
    GetItsiThresholds.execute()
