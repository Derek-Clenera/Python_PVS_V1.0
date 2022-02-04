# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 08:53:50 2021

Collection of functions to call within main, for battery degradation and array 
population

@author: Derek Ackerman
"""

#%% Functions
def populate_8760(file_name):
    """
    Function to read in and configure an 8760 from pvsyst
    
    Parameters
    ----------
    file_name : string
        name of PV-Syst output for the applicable case

    Returns
    -------
    array_dict : dictionary
        dictionary with inverter losses, and eArrayMPP hourly data for 1 year
        
    """
    import os
    import pandas as pd
    import numpy as np
    
    # set working directory for the PV-Syst file
    script_dir = 'C:\\Users\\Derek Ackerman\\Documents\\Python_ESS_cleaned_up\\pv_syst_files\\'
    # TODO: depending on the PV-Syst output, the header size can differ, despite 
    # The incoming file appearing identical in Excel
    # df_8760 = pd.read_csv(os.path.join(script_dir, file_name), encoding = "ISO-8859-1", engine='python', header=[10])
    # df_8760 = df_8760.drop(labels=[0,1])
    # Read in the excel .csv, saving the applicable columns, array energy as well as inverter losses
    df_8760 = pd.read_csv(os.path.join(script_dir, file_name), 
                          encoding = "ISO-8859-1", 
                          engine='python', 
                          header=[8])
    df_8760 = df_8760.drop(labels=[0])
    
    array_dict = {
                  # 'array energy':np.squeeze(df_8760['EOutInv'].to_numpy(dtype=float)),
                  'array energy': np.squeeze(df_8760['EArrMPP'].to_numpy(dtype=float)), 
                  'inverter losses': df_8760['IAMLoss'].to_numpy(dtype=float),
                  'array_voltage': df_8760['UArray'].to_numpy(dtype=float)}
    
    return array_dict


def module_degradation(module_dictionary):
    """
    Function to calculate module degradation by interpolating over the annual degradation 
    for the module used in the project.

    Parameters
    ----------
    module_dictionary : dictionary
        module parameters for degradation and life of module used in simulation

    Returns
    -------
    deg_H : np_array
        numpy array of hourly degradation

    """
    # TODO: check with start for array losses / degradation prior to COD
    annual_deg = module_dictionary['degradation']   # annual degradation %
    module_life = module_dictionary['life']         # years the module lasts
    deg_H = []           # create an hourly array full of nan
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_counter = 0
    deg_monthly = 1
    for i in range(0,module_life):
        for days in month_days:
            deg_monthly = 1 - (annual_deg/12)*month_counter   # matlab degradation
            for day in range(0, days):
                for hour in range(0,24):
                    deg_H.append(deg_monthly)
            month_counter+=1 
    
    return deg_H

def inv_output(array_energy, array_voltage):
    import inv_n_interp as inv_losses
    import numpy as np
    
    inv_output = np.zeros((len(array_energy)))
    for i in range(0,len(array_energy)):
        inv_output[i] = inv_losses(array_energy[i],array_voltage[i])
    return inv_output
    
def define_cases(components,
                 module_deg, 
                 array_energy,
                 batt_deg,
                 POI, 
                 dc_ac, 
                 inv_np, 
                 pcs, 
                 batt_hour,
                 aug_sched = []):
    """
    function to populate case combinations for DC/AC ratio, Inverter total nameplate,
    PCS total nameplate, and battery total hours

    Parameters
    ----------
    components : dictionary
        component models used for simulation, passed into functions used within the case creation
    module_deg : numpy array
        hourly degradation over the life of the solar panels
    array_energy : numpy array
        8760 X array life hourly array of PV-Syst simulation for the site location
    batt_deg : dict
        hourly capacity and round trip efficiency for the battery
    POI : int
        interconnection value (MW)
    dc_ac : list
        start, stop, step for DC/AC ratio range for case simulations
    inv_np : list
        start, stop, step for inverter nameplate range for case simulations
    pcs : list
        start, stop, step for PCS nameplate (battery capacity MW) range for case simulations
    batt_hour : list
        start, stop, step for battery hour[s] range for case simulations
    aug_sched : list
        list of year, and amount for battery system augmentation, default value of zero

    Returns
    -------
    case_list : dict
        dictionary of named case runs displaying pertinent info, to be 
         accessed by index to simplify use
         holds the following:
             array energy
             battery capacity
             battery hour
             battery power
             dc/ac ratio
             degraded array energy
             inverter nameplate
             limits
             losses
             PCS nameplate
             POI
    """
    import helper_functions as hf
    import monthly_battery_functions as batt
    import losses as loss
    import numpy as np

    case_list = {}
    i = 1
    # TODO: Matlab normalizes the array energy after applying degradation, is this good practice?
    array_norm = (array_energy/max(array_energy))*POI   # normalize array energy to model different DC/AC ratios
    # create variables to cycle through
    dcac_cases = hf.case_steps(dc_ac[0], 
                               dc_ac[1], 
                               dc_ac[2])            # DC/AC ratio, modules to POI rating
    inv_np_cases = hf.case_steps(inv_np[0], 
                                 inv_np[1], 
                                 inv_np[2])         # inverter nameplate (MW)
    pcs_np_cases = hf.case_steps(pcs[0], 
                                 pcs[1], 
                                 pcs[2])            # PCS nameplate (MW)
    batt_hour_cases = hf.case_steps(batt_hour[0], 
                                    batt_hour[1], 
                                    batt_hour[2])   # Battery hours (hours)
    
    for dc_ac in dcac_cases:
        for Inv in inv_np_cases:
            for PCS_np in pcs_np_cases:
                for Batt_hour in batt_hour_cases:
                        array_case = (array_norm*                   # define array energy for the run's dcac ratio 
                                      dc_ac)            
                        
                        array_deg_case = (array_energy*module_deg)
                        # Normalize the degraded array energy against the max value found
                        # and multiply by the DC/AC ratio and POI to allow for 
                        # multiple case runs using the same simulation output.
                        array_deg_case = (array_deg_case / max(array_deg_case))*dc_ac*POI 
                    
                        if len(aug_sched)==0:       # no augmentation
                            # calculate hourly battery capacity and rte for life of system
                            batt_cap_case = batt.battery_capacity(batt_deg,     
                                                                  Batt_hour, 
                                                                  PCS_np)
                            # calculate hourly max power, DOD nameplate, and  
                            # charge/discharge efficiency for life of system
                            batt_power_case = batt.battery_power(components['Batt'],        
                                                                 batt_cap_case)
                        else:                       # Augmentation schedule provided
                            # Set temporary container for augmentation
                            aug_temp = {}
                            capacity_installed = np.zeros(len(array_energy))
                            # For each augmentation in the schedule
                            for aug in aug_sched:
                                pre_aug = np.zeros(aug[0]*8760)  # create zeros prior to the year where the battery augmentation is installed.
                                # Find capacity, and dod_np over the life of the new battery.
                                cap_temp = batt.battery_capacity(batt_deg,     
                                                                  Batt_hour, 
                                                                  aug[1])
                                # Find power and rte limits over the life of the new battery.
                                power_temp = batt.battery_power(components['Batt'],        
                                                                 cap_temp)
                                # iterate through each of the battery limits.
                                for key in cap_temp:
                                    # Precede the values with zeros equal to the pre install period.
                                    cap_temp[key] = np.append(pre_aug, cap_temp[key])
                                    if len(cap_temp[key])<len(array_energy):
                                        # If it's not the final installation then add zeros to the end.
                                        cap_temp[key] = np.append(cap_temp[key],np.zeros(len(array_energy)-len(cap_temp[key])))
                                    elif len(cap_temp[key]) > len(array_energy):
                                        # If the installation runs past the simulation length, then clip anything past the end.
                                        cap_temp[key] = cap_temp[key][:len(array_energy)]
                                # Update the capacity total installed for each hour, to normalize augmentation rte and chg/discharge eta.
                                capacity_installed += np.where(cap_temp['capacity'] != 0,np.ones(len(cap_temp['capacity']))*aug[1], np.zeros(len(array_energy)))
                                for key in power_temp:
                                    # Precede the values with zeros equal to the pre-install period.
                                    power_temp[key] = np.append(pre_aug, power_temp[key])
                                    if len(power_temp[key])<len(array_energy):
                                        # If the augmentation does not go to the end of the simulation append zeros to the end.
                                        power_temp[key] = np.append(power_temp[key],np.zeros(len(array_energy)-len(power_temp[key])))
                                    elif len(power_temp[key]) > len(array_energy):
                                        # If the augmentation runs past the simulation clip excess values.
                                        power_temp[key] = power_temp[key][:len(array_energy)]
                                # Create a temporary dictionary holding     
                                aug_temp[aug[0]] = {'installed_cap':aug[1],'batt cap':cap_temp,'batt power':power_temp}
                            
                            cap_total = np.zeros(len(array_energy))
                            dod_total = np.zeros(len(array_energy))
                            p_total = np.zeros(len(array_energy))
                            rte_total = np.zeros(len(array_energy))
                            chg_total = np.zeros(len(array_energy))
                            # add all of the powers
                            for key in aug_temp:
                                cap_total += aug_temp[key]['batt cap']['capacity']
                                dod_total += aug_temp[key]['batt power']['DOD np']
                                p_total += aug_temp[key]['batt power']['max p']
                                rte_total += aug_temp[key]['batt cap']['rte']*aug_temp[key]['installed_cap']
                                chg_total += aug_temp[key]['batt power']['charge eta']*aug_temp[key]['installed_cap']
                            rte_total /= capacity_installed
                            chg_total /= capacity_installed
                            
                            batt_cap_case = {'capacity': cap_total,
                                             'rte': rte_total}
                            batt_power_case = {'max p': p_total,
                                               'charge eta': chg_total,
                                               'discharge eta': chg_total,
                                               'DOD np': dod_total}
         
                        # losses_case = hourly losses for power paths
                        # limits_case = hourly limits for array energy, 
                        # battery functions, and component limits for PV
                        losses_case, limits_case = loss.loss_calculations(array_deg_case,   
                                                             POI,                       
                                                             Inv,                       
                                                             PCS_np,
                                                             components,
                                                             batt_cap_case,
                                                             batt_power_case)
                        # Provide individual case run names for presentation and storage
                        # named case runs for differentiation and printing / naming excel outputs by case key
                        # name_temp = f'Case {i}: DC/AC ratio: {DC_AC}; PCS: {PCS_np} MWh; Inv_np: {Inv}; Battery hour: {Batt_hour}'
                        name_temp = f'Case {i}'
                        temp_dict = {'array energy':array_case,                 # normalized and updated array energy
                                     'degraded array energy':array_deg_case,    # degraded array energy
                                     'battery capacity': batt_cap_case,         # battery capacity dictionary
                                     'battery power': batt_power_case,          # battery power dictionary
                                     'losses': losses_case,                     # power path losses
                                     'limits': limits_case,                     # power path limits
                                     'POI':POI,                                 # interconnection rating (MW)
                                     'dc_ac ratio':dc_ac,                       # DC/AC ratio
                                     'Inv_np':Inv,                              # inverter nameplate (MW)
                                     'PCS nameplate':PCS_np,                    # PCS nameplate (MW)
                                     'battery hour':Batt_hour}                  # battery hours (hours)
                        # Update the case list dictionary with the new simulation case
                        case_list[name_temp] = temp_dict
                        i+=1

    return case_list
  