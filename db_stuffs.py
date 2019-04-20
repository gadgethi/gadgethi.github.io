import sqlite3
import doctest
import datetime
from pprint import pprint
from visualization import plot_data


# GLOBALS & CONSTANTS
# --------------------------------------------------------

DATABASE = '/Users/weitung/Documents/Arduino/608/Final_Project/server/project.db'

GROUPS = {
    'CSAIL': {'csail-0', 'csail-1'},
    'RLE'  : {'adam'},
    'SKRT' : set()
}


# DATABASE UTILS
# --------------------------------------------------------

def create_database(group_id):
    """
    Creates the database for storing sensor data while
    creating the table belong to the research group with
    ID `group_id` if it did not exist before
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # DB entries have format [sensor_id, distance, timestamp]
    query = '''CREATE TABLE IF NOT EXISTS {} (sensor_id text, distance number, timing timestamp);'''.format(group_id)
    c.execute(query)
    conn.commit() 
    conn.close()


def lookup_database(group_id):
    """
    Returns the contents of the DB for the table of
    group with group ID `group_id`
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # get everything from the table for group_id
    query = '''SELECT * FROM {};'''.format(group_id)
    things = c.execute(query).fetchall()
    conn.commit()
    conn.close() 
    return things


def timed_database_lookup(group_id, timestamp, window):
    """
    Returns the DB's contents for the table with group
    ID `group_id` that are within `window` seconds from
    the current time `timestamp`
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    delta = timestamp - datetime.timedelta(seconds = window)
    # get everything from DB table for group_id that has been
    # entered within the last `window` seconds
    query = '''SELECT * FROM {} WHERE timing > ?;'''.format(group_id)
    things = c.execute(query, (delta,)).fetchall()
    conn.commit()
    conn.close() 
    return things


def insert_into_database(group_id, sensor_id, distance, timestamp):
    """
    Inserts [`sensor_id`, `distance`, `timestamp`] into table with
    group id `group_id` that is assumed to already be in the DB
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = '''INSERT into {} VALUES (?, ?, ?);'''.format(group_id)
    c.execute(query, (sensor_id, distance, timestamp))
    conn.commit()
    conn.close() 


# HELPERS
# --------------------------------------------------------

def is_nonnegative_number(string, constructor = float):
    """
    Returns True if `string` represents a floating point
    or integer numeric value that is non-negative

    >>> is_nonnegative_number('')
    False
    >>> is_nonnegative_number('a')
    False
    >>> is_nonnegative_number('.')
    False
    >>> is_nonnegative_number('ofwnJWNFK')
    False
    >>> is_nonnegative_number('-1')
    False
    >>> is_nonnegative_number('2837948.2327839.238')
    False

    >>> is_nonnegative_number('0')
    True
    >>> is_nonnegative_number('1')
    True
    >>> is_nonnegative_number('1.0')
    True
    >>> is_nonnegative_number('0.1')
    True
    >>> is_nonnegative_number('3823872398')
    True
    >>> is_nonnegative_number('38238723.98')
    True
    """
    try:
        dist = constructor(string)
        return dist >= 0
    except Exception:
        return False


def sanitize_get(request):
    """
    Ensures the well-formedness of the given GET request.
    If everything is well-formed, returns dictionary of args,
    and otherwise will raise an Exception
    """
    # require group_id for request
    if 'group_id' not in request['args']:
        raise Exception('Expected group_id as part of the GET request')
    # require valid & registered group_id
    elif request['values']['group_id'] not in GROUPS:
        raise Exception('Expected given group_id to be registered. Please register your group')
    group_id = request['values']['group_id']

    # check for user-specified window in seconds
    window = None
    if 'window' in request['args']:
        # window must be a non-negative int
        if is_nonnegative_number(request['values']['window'], constructor = int):

            window = int(request['values']['window'])
        else:
            raise Exception('Expected given window size to be a non-negative int representing seconds')

    # return dictionary of data from the request
    return {
        'group_id': group_id,
        'window'  : window
    }


def sanitize_post(request):
    """
    Ensures the integrity of the incoming POST request
    If everything is well-formed, returns dictionary of
    group_id, sensor_id, and distance.
    Otherwise, raises an Exception
    """
    # must be urlencoded form
    if 'form' not in request:
        raise Exception('Expected urlencoded form with data in POST body')

    # require group_id for request
    if 'group_id' not in request['form']:
        raise Exception('Expected group_id as part of POST request body')
    # require group_id to be in the recognized GROUPS
    elif request['form']['group_id'] not in GROUPS:
        raise Exception('Expected group_id to be a recognized group. Please register your group')
    group_id = request['form']['group_id']
    
    # require sensor_id for request
    if 'sensor_id' not in request['form']:
        raise Exception('Expected sensor_id as part of POST request body')
    # require sensor_id to be a registered sensor
    elif request['form']['sensor_id'] not in GROUPS[group_id]:
        raise Exception('Expected this sensor to be part of the given group')
    sensor_id = request['form']['sensor_id']

    # require distance for request
    if 'distance' not in request['form']:
        raise Exception('Expected distance as part of POST request body')
    # require distance to be a numeric quantity
    elif not is_nonnegative_number(request['form']['distance']):
        raise Exception('Expected distance to be a non-negative numeric quantity')
    distance = float(request['form']['distance'])

    # return dictionary of data from the request
    return {
        'group_id' : group_id,
        'sensor_id': sensor_id,
        'distance' : distance
    }


def format_db_data(db_data, group_id):
    """
    Returns a nicely formatted string representing
    the `db_data` extracted from the DB of sensor data
    for the group with group ID `group_id`
    """
    # edge case: empty db_data
    if len(db_data) == 0:
        return 'NO DATA FOUND IN THE DB'

    # header of the data
    out = ['GROUP, SENSOR, DISTANCE, TIMESTAMP']

    # actual data from db
    for row in db_data:
        sensor_id, distance, timestamp = row
        out.append('{}, {}, {}, {}'.format(group_id, sensor_id, distance, timestamp))

    return '\n'.join(out)


# MAIN REQUEST HANDLER
# --------------------------------------------------------

def handle_get(request, timestamp):
    """
    GETs the sensor data of the specified group. Can
    optionally specify the window of time to get as a reference.
    For example, for a window of 100 seconds, this
    will try to get and return the sensor data for the last
    100 seconds. If no window is specified, pulls all data
    """
    #return """<div><img src="http://608dev.net/sandbox/sc/weitung/project/images/ihouse.jpg"></img></div>"""
    try:
        # get data from GET request
        data = sanitize_get(request)
        group_id, window = data['group_id'], data['window']

        # no window specified ==> all DB entries
        if window is None:
            db_data = lookup_database(group_id)
        # window specified ==> get last `windows` 
        # many seconds worth of data
        else:
            db_data = timed_database_lookup(group_id, timestamp, window)

        plot_data(db_data, group_id, display=True)

        # return pretty data
        return format_db_data(db_data, group_id)

    except Exception as e:
        return '\nFAILED:\n\t' + str(e)


def handle_post(request, timestamp):
    """
    POSTs sensor data to the table corresponding to the
    group that sent this request. Requires that the group
    be recognized as a member of the GROUPS constant
    """
    try:
        # get data from the POST request
        data = sanitize_post(request)
        group_id, sensor_id, distance = data['group_id'], data['sensor_id'], data['distance']

        # insert the data into the DB
        insert_into_database(group_id, sensor_id, distance, timestamp)
        return '\nSUCCESSFULLY ENTERED DATA INTO DB'
    
    except Exception as e:
        return '\nFAILED:\n\t' + str(e)

def local_db_test_init():
    """
    This is the initialization for local database 
    server testing. It creates all the necessary tables
    in the database
    """
    for group in GROUPS:
        create_database(group)


def request_handler(request):
    """
    Main request handler for receving and responding
    to GET and POST requests from groups' sensors
    """
    # get current time stamp
    timestamp = datetime.datetime.now()

    # create the DB with a table for each group
    for group in GROUPS:
        create_database(group)

    # handle POST
    if request['method'] == 'POST':
        return handle_post(request, timestamp)
    
    # handle GET
    elif request['method'] == 'GET':
        return handle_get(request, timestamp)

    # unknown request type
    else:
        return 'Unknown request format. Expected either GET or POST'


if __name__ == '__main__':
    doctest.testmod()
    pass