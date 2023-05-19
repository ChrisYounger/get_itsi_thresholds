import splunk.rest, splunk.search, json, math, pycron, time, traceback
from get_itsi_thresholds_app.search_command import SearchCommand
from datetime import datetime, timedelta
from collections import OrderedDict

class GetItsiThresholds(SearchCommand):

    def __init__(self, service=None, services=None, kpi=None, mode="", round="t", errors=""):
        self.service = service
        self.services = services
        self.kpi = kpi
        self.errors = errors
        self.mode = mode.lower()
        self.round = round.lower()[:1]
        # Initialize the class
        SearchCommand.__init__(self, run_in_preview=False, logger_name='get_itsi_thresholds_command')


    def handle_results(self, results, session_key, in_preview):

        def getServiceConfigFromSplunk(service_id):
            try:
                #response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service?fields="title,_key,kpis.title,kpis._key,kpis.adaptive_thresholds_is_enabled,kpis.time_variate_thresholds_specification"', sessionKey=self.session_key)
                response, content = splunk.rest.simpleRequest('/servicesNS/nobody/SA-ITOA/itoa_interface/service/' + service_id, sessionKey=self.session_key)
                #self.logger.info("Returned status: " + str(response.status))
                #self.logger.info("Received response (" + content + ")")
                if response.status != 200:
                    self.logger.warn("Unexpected error when retreiving service configuration (" + content + ")")
                    raise Exception(content)
                return json.loads(content)
            except Exception as ex:
                message = "An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
                self.logger.warn("Error retreiving thresholds. [" + message + "]")
                raise Exception("Error retreiving thresholds. [" + message + "]")

        def roundval(val):
            if self.round == "t":
                if val < 1 and val > -1:
                    r = str(round(val,3))
                elif val < 10 and val > -10:
                    r = str(round(val,2))
                elif val < 100 and val > -100:
                    r = str(round(val,1))
                else:
                    r = str(round(val,0))
                if "." in r:
                    r = r.rstrip('0').rstrip('.')
                return r
            return str(val)


        self.logger.info("Querying thresholds for service=\"" + str(self.service) + "\" kpi=\"" + str(self.kpi) + "\" in mode=\"" + self.mode + "\" rows_in=" + str(len(results)) + "")

        try:
            contentp = []
            if self.mode[0:3] == "now":
                if self.services is None:
                    contentp = getServiceConfigFromSplunk("")
                else:
                    for service_id in self.services.split(","):
                        service_id = service_id.strip()
                        if service_id != "":
                            response = getServiceConfigFromSplunk(service_id)
                            contentp.append(response)

            else:
                if self.service is None:
                    raise Exception("Missing \"service=\" argument ")
                if self.kpi is None:
                    raise Exception("Missing \"kpi=\" argument ")
                #self.logger.info("in_preview=" + str(in_preview))
                #self.logger.info("results=" + str(results))

                # check that the results have a _time field
                if len(results) > 0 and not "_time" in results[0]:
                    self.logger.warn("Cannot find the _time column in supplied data.")
                    raise Exception("Cannot find the _time column in supplied data.")

                response = getServiceConfigFromSplunk(self.service)
                contentp.append(response)

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

            KPIs = {}

            for service in contentp:
                # skip disabled services
                if service['enabled'] != 1:
                    continue
                for kpi in service["kpis"]:
                    #self.logger.error("Found kpi: " + kpi["_key"])
                    if not self.kpi is None and kpi["_key"] != self.kpi:
                        continue
                    # skip health score KPIs
                    if kpi["_key"][0:5] == "SHKPI":
                        continue
                
                    #self.logger.info("This is the KPI we need")

                    dpolicy = "UNKNOWN_POLICY"
                    dmin = ""
                    dmax = ""
                    draw = ""
                    dthreshold = []
                    dseverity = []
                    dcolor = []

                    if "time_variate_thresholds" in kpi and not kpi["time_variate_thresholds"]:
                        dpolicy = ""
                        dseverity.append(kpi["aggregate_thresholds"]["baseSeverityLabel"])
                        dcolor.append(kpi["aggregate_thresholds"]["baseSeverityColor"])
                        dmin = roundval(kpi["aggregate_thresholds"]["renderBoundaryMin"])
                        dmax = roundval(kpi["aggregate_thresholds"]["renderBoundaryMax"])
                        if self.mode == "raw":
                            draw = json.dumps(kpi["aggregate_thresholds"], indent=4, sort_keys=True)
                        for threshold in kpi["aggregate_thresholds"]["thresholdLevels"]:
                            dthreshold.append(roundval(threshold["thresholdValue"]))
                            dseverity.append(threshold["severityLabel"])
                            dcolor.append(threshold["severityColor"])

                    elif "default_policy" in kpi["time_variate_thresholds_specification"]["policies"]:
                        dpolicy = "default_policy"
                        dseverity.append(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["baseSeverityLabel"])
                        dcolor.append(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["baseSeverityColor"])
                        dmin = roundval(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["renderBoundaryMin"])
                        dmax = roundval(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["renderBoundaryMax"])
                        if self.mode == "raw":
                            draw = json.dumps(kpi["time_variate_thresholds_specification"]["policies"]["default_policy"], indent=4, sort_keys=True)
                        for threshold in kpi["time_variate_thresholds_specification"]["policies"]["default_policy"]["aggregate_thresholds"]["thresholdLevels"]:
                            dthreshold.append(roundval(threshold["thresholdValue"]))
                            dseverity.append(threshold["severityLabel"])
                            dcolor.append(threshold["severityColor"])

                    KPIs[kpi["_key"]] = {
                        'service_id': service["_key"],
                        'houroffsets': [],
                        'policies': [],
                        'thresholds': [],
                        'severities': [],
                        'colors': [],
                        'rawdata': [],
                        'boundarymin': [],
                        'boundarymax': [],
                        'policytitle': []
                    }

                    for i in range(0,168):
                        KPIs[kpi["_key"]]['houroffsets'].append(str(i))
                        KPIs[kpi["_key"]]['policies'].append(dpolicy)
                        KPIs[kpi["_key"]]['thresholds'].append(dthreshold)
                        KPIs[kpi["_key"]]['severities'].append(dseverity)
                        KPIs[kpi["_key"]]['colors'].append(dcolor)
                        KPIs[kpi["_key"]]['rawdata'].append(draw)
                        KPIs[kpi["_key"]]['boundarymin'].append(dmin)
                        KPIs[kpi["_key"]]['boundarymax'].append(dmax)
                        KPIs[kpi["_key"]]['policytitle'].append("Default")

                    if kpi["time_variate_thresholds"]:
                        for policy in kpi["time_variate_thresholds_specification"]["policies"]:
                            #res.append("Policy:" + policy)
                            #res.append("Policy Title:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["title"])
                            #res.append("Policy Type:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["policy_type"])
                            #res.append("Policy baseSeverityLabel:" + kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"])
                            thresStr = []
                            statusStr = [kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityLabel"]]
                            colorStr = [kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["baseSeverityColor"]]
                            for threshold in kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["thresholdLevels"]:
                                thresStr.append(roundval(threshold["thresholdValue"]))
                                statusStr.append(threshold["severityLabel"])
                                colorStr.append(threshold["severityColor"])

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
                                        KPIs[kpi["_key"]]['policies'][hr_offset] = policy
                                        KPIs[kpi["_key"]]['thresholds'][hr_offset] = thresStr
                                        KPIs[kpi["_key"]]['severities'][hr_offset] = statusStr
                                        KPIs[kpi["_key"]]['colors'][hr_offset] = colorStr
                                        KPIs[kpi["_key"]]['boundarymin'][hr_offset] = roundval(kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["renderBoundaryMin"])
                                        KPIs[kpi["_key"]]['boundarymax'][hr_offset] = roundval(kpi["time_variate_thresholds_specification"]["policies"][policy]["aggregate_thresholds"]["renderBoundaryMax"])
                                        KPIs[kpi["_key"]]['policytitle'][hr_offset] = kpi["time_variate_thresholds_specification"]["policies"][policy]["title"]
                                        KPIs[kpi["_key"]]['rawdata'][hr_offset] = rraw
                                        if rem_duration < 1:
                                            rem_duration = int(int(timeblock[1]) / 60)

            if self.mode[0:3] == "now":
                data_hr_offset_now = ((int(time.time()) // 3600) - 120) % 168 # this was previously 96
                extra_hours = 0
                mode_parts = self.mode.split("+")
                if len(mode_parts) == 2:
                    extra_hours = int(mode_parts[1])
                data_hr_offsets = [data_hr_offset_now]
                for ho in range(0,extra_hours):
                    data_hr_offsets.append((data_hr_offset_now + 1 + ho) % 168)
                for kpi in KPIs:
                    for data_hr_offset in data_hr_offsets:
                        row = OrderedDict()
                        results.append(row)
                        row['service_id'] = KPIs[kpi]['service_id']
                        row['kpi_id'] = kpi
                        if self.mode[0:11] == "nowextended" or len(data_hr_offsets) > 1:
                            row['hour'] = KPIs[kpi]['houroffsets'][data_hr_offset]
                        if self.mode[0:11] == "nowextended":
                            row['policy'] = KPIs[kpi]['policytitle'][data_hr_offset]
                            row['min'] = KPIs[kpi]['boundarymin'][data_hr_offset]
                            row['max'] = KPIs[kpi]['boundarymax'][data_hr_offset]
                        thstring = ""
                        thlength = len(KPIs[kpi]['thresholds'][data_hr_offset])
                        for idx, val in enumerate(KPIs[kpi]['severities'][data_hr_offset]):
                            if self.mode[0:11] == "nowextended":
                                row['severity' + str(idx)] = val
                            thstring += val
                            if idx < thlength:
                                thstring += "," + KPIs[kpi]['thresholds'][data_hr_offset][idx] + ","
                        if self.mode[0:11] == "nowextended":
                            for idx, val in enumerate(KPIs[kpi]['colors'][data_hr_offset]):
                                row['color' + str(idx)] = val
                            for idx, val in enumerate(KPIs[kpi]['thresholds'][data_hr_offset], 1):
                                row['threshold' + str(idx)] = val
                        row['thresholds'] = thstring;

            else:
                # if we didnt find 168 time blocks then we could not find the KPi
                if not self.kpi in KPIs:
                    self.logger.warn("Unable to find KPI. is kpi id correct?")
                    raise Exception("Unable to find KPI. is kpi id correct?")

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
                        data_hr_offset = ((int(row["_time"]) // 3600) - 120) % 168
                    # dump the raw json
                    if self.mode == "raw":
                        row['thresholds'] = KPIs[self.kpi]['rawdata'][data_hr_offset]
                    # dump each threshold as a column
                    elif self.mode == "columns":
                        row['hour'] = KPIs[self.kpi]['houroffsets'][data_hr_offset]
                        row['policy'] = KPIs[self.kpi]['policytitle'][data_hr_offset]
                        row['min'] = KPIs[self.kpi]['boundarymin'][data_hr_offset]
                        row['max'] = KPIs[self.kpi]['boundarymax'][data_hr_offset]
                        for idx, val in enumerate(KPIs[self.kpi]['severities'][data_hr_offset]):
                            row['severity' + str(idx)] = val
                        for idx, val in enumerate(KPIs[self.kpi]['colors'][data_hr_offset]):
                            row['color' + str(idx)] = val
                        for idx, val in enumerate(KPIs[self.kpi]['thresholds'][data_hr_offset], 1):
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
                        for idx, val in enumerate(KPIs[self.kpi]['severities'][data_hr_offset]):
                            row["regions"] += str(val) + "=" + str(KPIs[self.kpi]['colors'][data_hr_offset][idx]) # + " " + str(idx) + " " + str(len(thresholds[data_hr_offset]))
                            if (idx < len(KPIs[self.kpi]['thresholds'][data_hr_offset])):
                                row["regions"] += "," + str(KPIs[self.kpi]['thresholds'][data_hr_offset][idx]) + ","

            self.logger.info("Returning " + str(len(results)) + " results")
            # output the data
            self.output_results(results)
        except Exception as ex:
            if self.errors == "ignore":
                self.output_results(results)
            else:
                message = str(traceback.format_exc())
                raise Exception("Bad: [" + message + "]")
            

if __name__ == '__main__':
    GetItsiThresholds.execute()
