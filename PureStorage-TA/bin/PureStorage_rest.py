"""
Description: PureStorage modular input script which fetch data from purestorage rest api's and dumps data into splunk
"""

# Imports
import json
import os
import time
import sys
import traceback
import logger
from dateutil import tz
from datetime import datetime
from logger.config import FILE_NAME, FILE_SIZE, BACKUP_FILES_COUNT, LEVEL, LOGGER_NAME
from logger import setUpLogger
from splunklib.modularinput import *
import splunklib.client as client
from purestorage import FlashArray

# Constants
HERE = tz.tzlocal()
SOURCE = tz.gettz('UTC')
TT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Home/app directory paths
SPLUNK_HOME = os.environ.get('SPLUNK_HOME')
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(SPLUNK_HOME, 'var', 'log', 'splunk', 'purestorage')

# Configuring logs
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)
logger = setUpLogger(logger_name=LOGGER_NAME, base_dir=LOG_DIR, filename=FILE_NAME, level=LEVEL,
                     backupCount=BACKUP_FILES_COUNT, maxBytes=FILE_SIZE)


def merge_lists(list1, list2, key):
    """
    Description: Merge two lists base on key
    Parameters: list1: first list
                list2: second list
    Return: List
    """
    merged = {}
    for item in list1 + list2:
        if item[key] in merged:
            merged[item[key]].update(item)
        else:
            merged[item[key]] = item
    return merged.values()


def update_log_state(details, input_name, name):
    """
    Description: Filter out recent log data state and update log state
    Parameters: details: input data
                name: name of source
    Return: filter input data
    """
    log_state_dir = os.path.join(APP_DIR, 'logstate')
    if not os.path.exists(log_state_dir):
        os.mkdir(log_state_dir)
    if os.path.exists(os.path.join(log_state_dir, 'input.json')):
        with open(os.path.join(log_state_dir, 'input.json'), 'r+') as f:
            f.seek(0)
            data = json.loads(f.read())
            if input_name in data:
                details = filter(lambda x: x['opened'] > data.get(input_name).get(name), details)
                if details:
                    data[input_name][name] = details[-1].get("opened")
            else:
                temp = {input_name: {"log_alert": None, "log_login": None, "log_audit": None}}
                temp[input_name][name] = details[-1].get("opened")
                data.update(temp)
            f.seek(0)
            json.dump(data, f, sort_keys=True, indent=4)
            f.truncate()
        return details
    else:
        with open(os.path.join(log_state_dir, 'input.json'), "wb") as f:
            temp = {input_name: {"log_alert": None, "log_login": None, "log_audit": None}}
            temp[input_name][name] = details[-1].get("opened")
            f.write(json.dumps(temp))
            return details


def convert_to_float(str_time):
    """
    Description: Covert date into float format
    Parameter: str_time: Time in string format
    Return: Time
    """
    t = time.strptime(str_time, TT_FORMAT)
    utcdate = datetime.fromtimestamp(time.mktime(t))
    gmt = utcdate.replace(tzinfo=SOURCE)
    gmt_local = gmt.astimezone(HERE)
    return time.mktime(gmt_local.timetuple())


def remove_duplicates(alerts, type):
    """
    Description: Method remove duplicates event from data
    Parameter: data: event data
    Return: list of dict
    """
    temp = []
    if type == "log_login":
        for alert in alerts:
            flag = 0
            for row in temp:
                if row.get('component_type') == alert.get('component_type') and row.get('event') == alert.get('event'):
                        flag = 1
            if flag == 0:
                temp.append(alert)
    else:
        for alert in alerts:
            flag = 0
            for row in temp:
                if row.get('component_name') == alert.get('component_name') and row.get('component_type') == alert.get('component_type') and row.get('event') == alert.get('event'):
                    if "closed" in alert:
                        break
                    else:
                        flag = 1
            if flag == 0:
                temp.append(alert)
    return temp


class Source:
    """
    Description: Class maintain flash array source details
    """

    source_array = "Array"
    source_volume = "Volumes"
    source_host = "Hosts"
    source_alert_logs = "Logs_Alerts"
    source_alert_login = "Logs_Login"
    source_alert_audit = "Logs_Audit"
    source_pgroup = "Pgroups"
    source_snapshots = "Snapshots"
    sourcetype = "PureStorage_REST"


class PureStorageREST(Script):
    """
    Description: Class responsible for generating modular inputs from flash array real time data
    """
    # Define some global variables
    MASK = "<nothing to see here>"
    APP = __file__.split(os.sep)[-3]
    USERNAME = None
    CLEAR_PASSWORD = None

    def get_scheme(self):
        """
        Description: Get scheme and arguments
        """

        # Setup scheme
        scheme = Scheme("PureStorage Array Rest API")
        scheme.description = "Streams information about array from PureStorage REST API"
        scheme.use_external_validation = True

        # Add arguments
        array_argument = Argument("Array")
        array_argument.data_type = Argument.data_type_string
        array_argument.description = "IP address of PureStorage array"
        array_argument.required_on_create = True
        scheme.add_argument(array_argument)

        username_argument = Argument("Username")
        username_argument.data_type = Argument.data_type_string
        username_argument.description = "PureStorage array username"
        username_argument.required_on_create = True
        scheme.add_argument(username_argument)

        password_argument = Argument("Password")
        password_argument.data_type = Argument.data_type_string
        password_argument.description = "PureStorage array password"
        password_argument.required_on_create = True
        scheme.add_argument(password_argument)

        return scheme

    def write_events(self, ew, array, data, input_name, source, sourcetype):
        """
        Description: Dumps data into splunk
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
                    source: source name
                    sourcetype: source type
        """

        if isinstance(data, dict):
            raw_event = Event()
            if data.get('time'):
                raw_event.time = convert_to_float(data.get('time'))
            if data.get('opened'):
                raw_event.time = convert_to_float(data.get('opened'))
            raw_event.stanza = input_name
            raw_event.source = source
            raw_event.host = array
            raw_event.data = json.dumps(data)
            raw_event.sourcetype = sourcetype
            ew.write_event(raw_event)
            return

        for row in data:
            raw_event = Event()
            if row.get('time'):
                raw_event.time = convert_to_float(row.get('time'))
                del row['time']
            if row.get('opened'):
                raw_event.time = convert_to_float(row.get('opened'))
                del row['opened']
            raw_event.stanza = input_name
            raw_event.source = source
            raw_event.host = array
            raw_event.data = json.dumps(row)
            raw_event.sourcetype = sourcetype
            ew.write_event(raw_event)

    def get_array_details(self, ew, connection, array, input_name):
        """
        Description: Fetch flash array details
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
        """

        logger.info('Getting array details from array REST service')
        array_details = connection.get()
        array_details.update(connection.get(space=True)[0])
        array_details.update(connection.get(action='monitor')[0])
        self.write_events(ew, array, array_details, input_name, source=Source.source_array,
                          sourcetype=Source.sourcetype)

    def get_volume_details(self, ew, connection, array, input_name):
        """
        Description: Fetch flash array volume details
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
                    performance: flag
                    capacity: flag
        """

        logger.info('Getting volume details from array REST service')
        volumes_details = connection.list_volumes()
        volumes_details = merge_lists(volumes_details, connection.list_volumes(space=True), 'name')
        volumes_details = merge_lists(volumes_details, connection.list_volumes(action='monitor'), 'name')
        for row in volumes_details:
            source = row.get('source')
            del row['source']
            row['source_volume'] = source
        self.write_events(ew, array, volumes_details, input_name, source=Source.source_volume,
                          sourcetype=Source.sourcetype)

    def get_volume_snap_details(self, ew, connection, array, input_name):
        """
        Description: Fetch flash array volume snapshots details
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
        """

        logger.info('Getting volume snap details from array REST service')
        # Getting protection group information
        snapshot_details = []
        pgroup_list = connection.list_pgroups()
        space_details = connection.list_pgroups(space=True)
        pgroup_list = merge_lists(pgroup_list, space_details, "name")
        for row in pgroup_list:
            del row['source']
        pgroup_list.append({'hgroups': None, 'hosts':None, 'name': 'Other', 'snapshots': 0,'targets': None, 'volumes':None})
        self.write_events(ew, array, pgroup_list, input_name, source=Source.source_pgroup,
                          sourcetype=Source.sourcetype)
        pgroup_list = map(lambda x: x['name'], pgroup_list)
        pgroup_list.remove('Other')
        # Getting snapshots with respect to pgroup
        for group in pgroup_list:
            temp_snap = connection.list_volumes(snap=True, pgrouplist=group)
            temp_space = connection.list_volumes(snap=True, pgrouplist=group, space=True)
            temp = merge_lists(temp_snap, temp_space, "name")
            for row in temp:
                row.update({"pgroup": group})
                row['volume'] = row['source']
                del row['source']
            snapshot_details.extend(temp)

        all_snap = connection.list_volumes(snap=True)
        all_space = connection.list_volumes(snap=True, space=True)
        temp = merge_lists(all_snap, all_space, 'name')

        other_snap = []
        for snap in temp:
            if not str(snap['name']).startswith(tuple(pgroup_list)):
                snap.update({"pgroup": "Other"})
                snap['volume'] = snap['source']
                del snap['source']
                other_snap.append(snap)
        snapshot_details.extend(other_snap)
        self.write_events(ew, array, snapshot_details, input_name, source=Source.source_snapshots,
                          sourcetype=Source.sourcetype)

    def get_host_details(self, ew, connection, array, input_name):
        """
        Description: Fetch flash array host details
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
                    performance: flag
                    capacity: flag
        """

        logger.info('Getting host details from array REST service')
        hosts_details = connection.list_hosts(all=True)
        for row in hosts_details:
            row.update()
        self.write_events(ew, array, hosts_details, input_name, source=Source.source_host, sourcetype=Source.sourcetype)
        hosts_details = connection.list_hosts(space=True)
        self.write_events(ew, array, hosts_details, input_name, source=Source.source_host, sourcetype=Source.sourcetype)

    def get_message_details(self, ew, connection, array, input_name):
        """
        Description: Fetch flash array alert details
        Parameters: ew: log object
                    connection: array connection object
                    array: array name
                    input_name: forwarder name
        """

        # Alert logs
        logger.info('Getting alert and messages details from array REST service')
        alert_details = connection.list_messages()
        if alert_details:
            alert_details = update_log_state(alert_details, input_name, "log_alert")
        alert_details = remove_duplicates(alert_details, "log_alert")
        self.write_events(ew, array, alert_details, input_name, source=Source.source_alert_logs,
                          sourcetype=Source.sourcetype)

        # Audit logs
        logger.info('Getting audit alert and messages details from array REST service')
        alert_details = connection.list_messages(audit=True)
        if alert_details:
            alert_details = update_log_state(alert_details, input_name, "log_audit")
        self.write_events(ew, array, alert_details, input_name, source=Source.source_alert_audit,
                          sourcetype=Source.sourcetype)

        # Login logs
        logger.info('Getting login alert and messages details from array REST service')
        alert_details = connection.list_messages(login=True)
        if alert_details:
            alert_details = update_log_state(alert_details, input_name, "log_login")
        self.write_events(ew, array, alert_details, input_name, source=Source.source_alert_login,
                          sourcetype=Source.sourcetype)

    def encrypt_password(self, username, password, session_key):
        try:
			# If the credential already exists, delte it.
            for storage_password in self.service.storage_passwords:
                if storage_password.username == username:
                    self.service.storage_passwords.delete(username=storage_password.username)
                    break

            # Create the credential.
            self.service.storage_passwords.create(password, username)
        except Exception as e:
            raise Exception("An error occurred updating credentials. Please ensure your user account has admin_all_objects and/or list_storage_passwords capabilities. Details: %s" % str(e))

    def mask_password(self, session_key, username):
        try:
            kind, input_name = self.input_name.split("://")
            item = self.service.inputs.__getitem__((input_name, kind))
            kwargs = {
                "Username": username,
                "Password": self.MASK
            }
            item.update(**kwargs).refresh()
        except Exception as e:
            raise Exception("Error updating inputs.conf: %s" % str(e))

    def get_password(self, session_key, username):
		# Retrieve the password from the storage/passwords endpoint	
		for storage_password in self.service.storage_passwords:
			if storage_password.username == username:
				return storage_password.content.clear_password

    def stream_events(self, inputs, ew):
        """
        Description: Splunk Enterprise calls the modular input,
                     streams XML describing the inputs to stdin,
                     and waits for XML on stdout describing events.
        """	

        for self.input_name, self.input_item in inputs.inputs.iteritems():
            array = self.input_item["Array"]
            username = self.input_item["Username"]
            password = self.input_item["Password"]
            session_key = self._input_definition.metadata["session_key"]
            self.USERNAME = username
            try:
                # If the password is not masked, mask it.
                if password != self.MASK:
                    self.encrypt_password(username, password, session_key)
                    self.mask_password(session_key, username)

                self.CLEAR_PASSWORD = self.get_password(session_key, username)
            except Exception as e:
                ew.log("ERROR", "Error: %s" % str(e))

            ew.log("INFO",
                   "Starting PureStorage Array REST input processing:  ARRAY=%s USERNAME=%s" % (array, username))
            logger.info("Starting PureStorage Array REST input processing:  ARRAY=%s USERNAME=%s" % (array, username))
            try:
                connection = FlashArray(array, username, self.CLEAR_PASSWORD)

                logger.info("Flash Array connection successful")

                # Alert and messages details
                self.get_message_details(ew, connection, array, self.input_name)

                # Array details
                self.get_array_details(ew, connection, array, self.input_name)

                # Volume details
                self.get_volume_details(ew, connection, array, self.input_name)

                # Volume snapshot and protection group details
                self.get_volume_snap_details(ew, connection, array, self.input_name)

                # Host details
                self.get_host_details(ew, connection, array, self.input_name)

                logger.info("Modular input data dump successful")
            except Exception as e:
                ew.log("ERROR", "Error in modular input script Exception: %s" % e)
                logger.error('Error in modular input script Exception: %s' % e)
                logger.error(traceback.format_exc())
                raise e


if __name__ == "__main__":
    sys.exit(PureStorageREST().run(sys.argv))
