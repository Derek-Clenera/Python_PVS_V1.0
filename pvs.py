
# -*- coding: utf-8 -*-
"""
collection of arbitrage functions for medium voltage AC coupled system

Created on Fri Sep 17 12:59:25 2021

@author: Derek Ackerman
"""
import numpy as np
import time 
import dispatch as nd
import gc 
    

def arbitrage(PV_min_energy_chg_threshold, ppa_min_delta, case_list, project_rates, batt_limit_POI, batt_hours_POI):
    """
    Function to reduce configuration page requirements to run simulations. Takes 
    the charge and arbitrage threshold variables and runs the each case simulation,
    updating the dictionary with the dispatch output as it goes through.

    Parameters
    ----------
    PV_min_energy_chg_threshold : float
        Minimum PV energy to charge the battery.
    ppa_min_delta : float
        Minimum delta between highest and lowest daily combined rate to charge 
        and discharge the battery
    case_list : dict
        Dictionary of all the cases to perform arbitrage on.
    project_rates : dict
        Dictionary of hourly values for all rates, can be performed using only 
        the combined rate if necessary
    batt_limit_POI: int
        PCS limit at the POI.
    batt_hours_POI: int
        hours to dispatch at the POI limit.

    Returns
    -------
    None.

    """
    # iterate through each case in the simulation sweep.
    for key in case_list:
        start=time.time()
        # Calculate the minimum PV energy to charge the battery.
        PV_min_energy_chg = (max(case_list[key]['degraded array energy'])*
                                    PV_min_energy_chg_threshold)
        # Perform arbitrage for the simulation case.
        output = pvs_ac_mv(PV_min_energy_chg,
                                ppa_min_delta,
                                batt_limit_POI,
                                batt_hours_POI,
                                case_list[key]['degraded array energy'],
                                project_rates,
                                case_list[key]['POI'],
                                case_list[key]['losses'],
                                case_list[key]['limits'],
                                case_list[key]['battery capacity'],
                                case_list[key]['battery power'])
        # Update the case in the dictionary with the dispatch output.
        case_list[key]['dispatch output'] = output
        print(f'parameter declaration and full arbitrage time: {time.time()-start} seconds')
        # call the python garbage collector
        gc.collect()
        
def pvs_ac_mv(PV_min_energy_chg,
              ppa_min_delta,
              batt_limit_POI,
              batt_hours_POI,
              array_energy, 
              project_rates, 
              POI, 
              loss_dict, 
              limits_dict,
              batt_cap,
              batt_power):
    """
    Function to slice daily chunks from input arrays and run the arbitrage 
    function for the battery system

    Parameters
    ----------
    PV_min_energy_chg : float
        minimum array energy required to initiate charging for the battery.
    ppa_min_delta : int
        minimum daily delta between high and low rate to initiate arbitrage.
    batt_limit_POI: int
        PCS limit at the POI.
    batt_hours_POI: int
        hours to dispatch at the POI limit.
    array_energy : array
        Degraded array energy available to the inverters over the life of the modules.
    project_rates : array
        hourly rate data for the site / node. Currently running on combined rate
    POI : int
        Interconnection size in MW.
    loss_dict : dictionary
        dictionary accounting for losses in all flow paths for the simulation.
    limits_dict : dictionary
        dictionary holding limits for equipments for the simulation.
    batt_cap : dictionary
        dictionary holding capacity and round trip efficiency for the battery system
    batt_power : dictionary
        dictionary holding max power, charge and discharge eta, and dod_np for the battery system.

    Returns
    -------
    dispatch_output : dictionary
        dictionary holding hourly outputs for the following data:
            PV only plant energy
            PVS POI output - PV
            PVS POI output - battery,
            battery SOC %
            battery SOC MWh
            node meter PVS
            node meter PV
            POI meter PVS
            POI meter PV
            battery charge state
            charge sequence
            discharge sequence
            hour
            inverter output
            clip harvesting

    """
    # Create empty output container, at this time only 12 values are used by 
    # the matlab code.
    output = np.empty([len(array_energy),15])
    start = time.time()
    # Prepare the case for dispatch, converting dictionary held values to a 
    # 35 year hourly array for addressing in simulation.
    dispatch_array = dispatch_prep(array_energy, 
                                   project_rates, 
                                   loss_dict, 
                                   limits_dict,
                                   batt_cap,
                                   batt_power)
    # Slice the full run array into 24 hour arrays and send them through the 
    # daily arbitrage function.
    for index in range(0,len(array_energy),24):
        # slice appropriate data from holders.
        daily_array = dispatch_array[index:index+24,:]
        # Determine if the rate delta for the day meets arbitrage requirements.
        arbitrage = (max(daily_array[:,2]) - min(daily_array[:,2])
                        > ppa_min_delta)
        # Run the mv-ac coupled dispatch function for each day.
        daily_out = nd.daily_arbitrage(arbitrage,
                                    POI,
                                    PV_min_energy_chg,
                                    ppa_min_delta,
                                    batt_limit_POI,
                                    batt_hours_POI,
                                    daily_array)
        # Update the output array in the correct index for each day.
        output[index:index+24,:] = daily_out
        # Create the output dictionary, assigning keys to columns in the array.
        dispatch_output = {
            'PV only plant energy': output[:,0],
            'PVS POI output - PV': output[:,1],
            'PVS POI output - battery': output[:,2],
            'battery SOC %': output[:,3],
            'battery SOC MWh': output[:,4],
            'node meter PVS': output[:,5],
            'node meter PV': output[:,6],
            'POI meter PVS': output[:,7],
            'POI meter PV': output[:,8],
            'battery charge state': output[:,9],
            'charge sequence': output[:,10],
            'discharge sequence': output[:,11],
            'hour': output[:,12],
            'inverter output': output[:,13],
            'clip harvesting': output[:,14]}
            
            
    return dispatch_output
        

def dispatch_prep(array_energy,
                  project_rates,
                  losses,
                  limits,
                  battery_capacity,
                  battery_power):
    # Create empty array to hold all variables.
    dispatch_array = np.empty([len(array_energy),25])
    """
    Function to convert simulation parameters from dictionary entries into a numpy array
    for faster access and the ability to run using Numba. 
    
    dispatch array format:
        0:      array energy
        1:      capacity rate
        2:      combined rate
        3:      energy rate
        4:      RA rate
        5:      REC rate
        6:      array energy inverter limited
        7:      array energy POI limited
        8:      battery charge power
        9:      battery discharge power
        10:     inverter limit PV power
        11:     PCS limit battery charge power
        12:     PCS limit battery discharge power
        13:     POI limit PV power
        14:     power limited by battery
        15:     array to battery
        16:     array to node meter
        17:     array to POI
        18:     battery to POI
        19:     charge eta (battery)
        20:     discharge eta (battery)
        21:     DOD np
        22:     max p
        23:     capacity (battery)
        24:     rte (battery)
        """
    dispatch_array[:,0] = array_energy
    dispatch_array[:,1] = project_rates['rate capacity']
    dispatch_array[:,2] = project_rates['rate combined']
    dispatch_array[:,3] = project_rates['rate energy']
    dispatch_array[:,4] = project_rates['rate RA']
    dispatch_array[:,5] = project_rates['rate REC']
    dispatch_array[:,6] = limits['array energy inverter limited']
    dispatch_array[:,7] = limits['array energy POI limited']
    dispatch_array[:,8] = limits['battery charge power']
    dispatch_array[:,9] = limits['battery discharge power']
    dispatch_array[:,10] = limits['inverter limit PV power']
    dispatch_array[:,11] = limits['PCS limit battery charge power']
    dispatch_array[:,12] = limits['PCS limit battery discharge power']
    dispatch_array[:,13] = limits['POI limit PV power']
    dispatch_array[:,14] = limits['power limited by battery']
    dispatch_array[:,15] = losses['array to battery']
    dispatch_array[:,16] = losses['array to node meter']
    dispatch_array[:,17] = losses['array to POI']
    dispatch_array[:,18] = losses['battery to POI']
    dispatch_array[:,19] = battery_power['charge eta']
    dispatch_array[:,20] = battery_power['discharge eta']
    dispatch_array[:,21] = battery_power['DOD np']
    dispatch_array[:,22] = battery_power['max p']
    dispatch_array[:,23] = battery_capacity['capacity']
    dispatch_array[:,24] = battery_capacity['rte']
    
    return dispatch_array