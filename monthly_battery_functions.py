# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 13:50:44 2021

@author: Derek Ackerman
"""

# monthly_battery_functions
#%% Imports
import numpy as np
import pandas as pd

def battery_degradation(battery, 
                        cycles_per_day):
    """
    calculate battery degradation using either c_365 or c_730 degradation curves from the model

    Parameters
    ----------
    battery : dict
        component model dictionary for battery, used for battery life and 
        degradation curves
    cycles_per_day : int
        select 1 or 2 cycles per day to determine which
        degradation curve to use

    Returns
    -------
    batt_degradation : dict
        dictionary containing hourly values for the following
            battery_rte:    float   round trip efficiency of the battery at each hour
            capacity:       float   degraded capacity in % for the battery at each hour
            
    """
    batt_life = int(battery['life'])    # cast as int, np array default type float64
    if(cycles_per_day == 1):
        deg_curve = battery['deg_c365']
    elif(cycles_per_day == 2):
        deg_curve = battery['deg_c730']
    else:
        return(print('selected cycles per day is invalid for current model'))
    # calculate calendar and throughput degradation over battery life
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    deg_temp = np.zeros(batt_life*12+1)     # establish empty hourly array.
    deg_temp[:] = np.nan                    # convert zeros to NAN for interpolation.
    rte_temp = deg_temp[:len(deg_temp)-1]   # 1 unit less since degradation trims final value, 
                                            # in order to interpolate properly.
    
    for i in range(batt_life):
        deg_temp[i*12] = deg_curve[i]                        # add known values.
    deg_temp[len(deg_temp)-1] = deg_curve[len(deg_curve)-1]  # add final value.
    df_temp = pd.DataFrame(data=deg_temp)
    df_temp = df_temp.interpolate()
    deg_m = df_temp.to_numpy(dtype=float)
    deg_m = deg_m[:len(deg_m)-1]
    batt_deg = np.zeros(batt_life*365*24)
    
    # calculate round trip efficiency hourly over battery .
    rte_temp[:] = np.nan
    rte_temp[0] = float(battery['rte_BOL'])                 # beginning of life n.
    rte_temp[len(rte_temp)-1] = float(battery['rte_EOL'])   # end of life n.
    # load into dataframe for interpolation
    df_rte_temp = pd.DataFrame(data=rte_temp)
    df_rte_temp = df_rte_temp.interpolate()
    rte_m = df_rte_temp.to_numpy(dtype=float)
    rte_deg = np.zeros(batt_life*365*24)
    
    # iterate over the degradation, loading each month with the same degradation value. 
    # over its length
    hourly_index = 0
    month_index = 0
    for year in range(batt_life):
        for days in month_days:
            for i in range(days*24):
                batt_deg[hourly_index] = deg_m[month_index]
                rte_deg[hourly_index] = rte_m[month_index]
                hourly_index += 1
            month_index += 1
    
    batt_degradation = {'battery capacity': batt_deg, 'rte': rte_deg}
    
    return batt_degradation


def battery_capacity(batt_deg,
                     batt_hour,
                     PCS_tot_np
                     ):
    """
    convert the degradation into capacity for the energy storage currently installed.

    Parameters
    ----------
    batt_deg : dict
        hourly degradation for the battery, and round trip 
        efficiency for the life of the battery.
    batt_hour : int
        hours of storage at nameplate for the energy storage 
        system for each case.
    PCS_tot_np : float
        nameplate for the battery storage system *note, for future 
        versions, the PCS nameplate should not be accounted, 
        instead use the number of containers for the augmentation.
        the funciton will be rewritten to accomodate. 

    Returns
    -------
    batt_cap : dict
        dictionary containing hourly values for the following:
            capacity:   float   hourly values for battery capacity accounting
                                for degradation
            rte:        float   hourly values for round trip efficiency 
                                accounting for degradation
                                
    """
    # battery degradation % * hours * total installed capacity (MW) for MWh output.
    batt_capacity = np.squeeze(batt_deg['battery capacity'] * batt_hour * PCS_tot_np)
    # create output dictionary holding hourly round trip efficiency and capacity.
    batt_cap = {'capacity': batt_capacity,
                'rte': np.squeeze(batt_deg['rte'])}

    return batt_cap


def battery_power(battery,
               batt_cap):
    """
    create hourly values for battery storage system characteristics 

    Parameters
    ----------
    battery : dict
        battery from component list for the case
    batt_cap : dict
        hourly values for round trip efficiency and capacity
        over the life of the battery

    Returns
    -------
    batt_power : dict
        dictionary containing hourly values for the following:
            max p:          float   max power for the battery
            charge eta:     float   charge efficiency 
            discharge eta:  float   discharge efficiency
            DOD np:         float   max allowable discharge accounting for 
                                    capacity and eta_DOD
        
    """
    # max power of the battery, equal to cp-rate times the capacity.
    batt_max_p = np.squeeze(batt_cap['capacity'] *
                            battery['cp'])
    # charge and discharge efficiency are square root of round trip.
    batt_chg_eta = np.squeeze(np.sqrt(batt_cap['rte']))
    batt_dischg_eta = batt_chg_eta
    # nameplate depth of discharge = capacity * max discharge
    batt_DOD_np = np.squeeze(batt_cap['capacity'] * battery['eta_DOD'])
    # create battery power output dictionary.
    batt_power = {
        'max p': batt_max_p,
        'charge eta': batt_chg_eta,
        'discharge eta': batt_dischg_eta,
        'DOD np': batt_DOD_np}
    
    return batt_power

def array_match(batt_power, batt_cap, array_length):
    """
    function to match array sizing with solar energy array length, pads with 
    zeros to allow for hourly math in the dispatch function

    Parameters
    ----------
    batt_power : dict
        DESCRIPTION.
    batt_cap : dict
        DESCRIPTION.
    array_length : int
        length (hourly) of array to match

    Returns
    -------
    batt_power : dict
        input padded with zeros
    batt_cap : dict
        input padded with zeros

    """
    # while augmentation is not present, function to pad arrays with zeros 
    # to match project life span
    for key in batt_power:
        if(len(batt_power[key]) < array_length):
            batt_power[key] = np.pad(batt_power[key],((0,array_length-len(batt_power[key]))),'constant')
    for key in batt_cap:
        if(len(batt_cap[key]) < array_length):
            batt_cap[key] = np.pad(batt_cap[key],((0,array_length-len(batt_cap[key]))),'constant')
    return batt_power, batt_cap
    
