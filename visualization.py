import numpy as np
import matplotlib.pyplot as plt
import doctest
import datetime
from globals import *

def format_timestamp(timestamp, time_dict, sensor_id):
    """
    Format the timestamp so that it's a integer counting
    from the first data of the sequence
    """
    time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").timestamp()

    try:
        bias = time_dict[sensor_id]['bias']
    except:
        bias = time
        time_dict[sensor_id] = {}
        time_dict[sensor_id]['bias'] = bias

    return time - bias


def update_dictionaries(data_entry, data_dict, time_dict):
    """
    Update the two dictionaries for plotting based on the
    row entries of the db_data.
    data_entry: a row in the db
    data_dict: keep track of the data points of all the sensors
    time_dict: keep track of all the timestamps for different sensors
    """
    sensor_id, distance, timestamp = data_entry
    time = format_timestamp(timestamp, time_dict, sensor_id)

    try:
        data_dict[sensor_id].append(distance)
        time_dict[sensor_id]['timestamp'].append(time)
    except:
        data_dict[sensor_id] = [distance]
        time_dict[sensor_id]['timestamp'] = [time]

def plot_sensor_data(group, sensor_id, data_dict, time_dict, display):
    """
    Plot the data points for one sensor
    """
    try:
        data_pts = data_dict[sensor_id]
        timestamps = time_dict[sensor_id]['timestamp']
        identifier = time_dict[sensor_id]['bias']
    except:
        return

    figure = plt.figure(sensor_id)
    plt.plot(timestamps, data_pts)

    # All the labeling on the graphs are done here
    starting_time = datetime.datetime.fromtimestamp(identifier)
    plt.xlabel("time (s) starting at "+str(starting_time))
    plt.ylabel("distance")
    plt.title("Group: "+str(group)+"; Sensor: "+str(sensor_id)+" Data")

    # Save the plot to file
    filename = "group_"+str(group)+"_sensor_"+str(sensor_id)+"_"+str(identifier)+".png"
    plt.savefig("graphs/"+filename)

    # Display the plot
    if display:
        plt.show(block=False)
        plt.pause(0.05)

    # Clear the graph for the next sensor
    plt.cla()
    plt.clf()


def plot_data(db_data, group_id, sensor=None, display=False):
    """
    Plot all the sensor data with a specific group id
    """
    sensors = GROUPS[group_id]  #Get all the sensors
    data_dict = {}              #For data points
    time_dict = {}              #For time stamps

    for row in db_data:
        update_dictionaries(row, data_dict, time_dict)
        
    if sensor == None:
        """
        If none of the sensors are specified, 
        Plot the data of all the sensors
        """
        for s in sensors:
            plot_sensor_data(group_id, s, data_dict, time_dict, display)
    else:
        plot_sensor_data(group_id, sensor, data_dict, time_dict, display)


if __name__ == '__main__':
    doctest.testmod()
    pass