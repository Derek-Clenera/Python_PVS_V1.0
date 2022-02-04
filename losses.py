# -*- coding: utf-8 -*-
def loss_calculations(PV_energy,
                      POI,
                      inv_np,
                      PCS_np,
                      components, 
                      batt_cap,
                      batt_power):
    """
    Function to calculate losses and limits on an hourly basis to transmission
    paths, and for key components in the dispatch function

    Parameters
    ----------
    PV_energy : float
        array of hourly array energy over the life of the project
    POI : int
        interconnection limit for the project in MW
    inv_np : float
        nameplate for all inverters combined on site in MW
    PCS_np : float
        nameplate for total storage system in MW
    components : dictionary
        components used in the project, containing 
        key attributes for loss calculations
    batt_cap : dictionary
        dictionary with battery capacity and round trip 
        efficiency
    batt_power : dictionary
        dictionary with hourly values over the life of the battery for 
        max power, charge efficiency, discharge efficiency, and nameplate depth
        of discdharge

    Returns
    -------
    loss_dict : dict
        dictionary containing hourly values for efficiencies for the 
        following paths:
            array to POI
            array to battery
            battery to POI
            array to node meter
            
    limits_dict : dict
        dictionary containing hard limits for the following components / pairs
            array energy inverter limited
            array energy POI limited 
            battery charge power
            battery discharge power
            inverter limit PV power *constant
            PCS limit battery charge power *constant
            PCS limit battery discharge power *constant
            POI limit PV power *constant
            Power limited by battery

    """
    import numpy as np
    # TODO: updated to monthly losses
    import monthly_battery_functions as batt

    # check to lengthen arrays to match size for entire dispatch function, 
    # lengthening battery paramaters to match size of array life, and 
    # setting all outside of battery life to zeros.
    array_length = components['Mod']['life'] * 365 * 24     # hourly by life of module.
    batt_power, batt_cap = batt.array_match(batt_power,     # match battery system parameters to length of array energy for dispatch.
                                            batt_cap, 
                                            array_length)
    # calculate array to POI losses based on diagram.
    arr_to_POI_temp = (components['ModCol']['eta']* 
                  components['Inv']['eta']*
                  components['MVT_Inv']['eta']*
                  components['MVCol_Inv']['eta']*
                  components['GSU']['eta'])
    arr_to_POI = np.repeat(arr_to_POI_temp, array_length, axis=0) # repeat array to match length of dispatch.
    # calculate array to battery losses based on diagram.
    arr_to_batt = (components['ModCol']['eta']*
                  components['Inv']['eta']*
                  components['MVT_Inv']['eta']*
                  components['MVCol_Inv']['eta']*
                  components['MVCol_PCS']['eta']*
                  components['MVT_PCS']['eta']*
                  components['PCS']['eta']*
                  components['BattCol']['eta']*
                  batt_power['charge eta'])
    # calculate battery to POI losses based on diagram.
    batt_to_POI = (batt_power['discharge eta']*
                   components['BattCol']['eta']*
                   components['PCS']['eta']*
                   components['MVT_PCS']['eta']*
                   components['MVCol_PCS']['eta']*
                   components['GSU']['eta'])
    # calculate array to node meter (at MVAC interconnection point) losses.
    arr_to_meter_temp = (components['ModCol']['eta']*
                      components['Inv']['eta']*
                      components['MVT_Inv']['eta']*
                      components['MVCol_Inv']['eta'])
    arr_to_meter = np.repeat(arr_to_meter_temp, array_length, axis=0)   # Match constant value to the correct length.
    # Compile dictionary for loss parameters.
    loss_dict = {'array to POI': arr_to_POI,
                 'array to battery': arr_to_batt,
                 'battery to POI': batt_to_POI,
                 'array to node meter': arr_to_meter}

    # calculate powers limited by inverter and POI ratings.
    inv_lim_PV_p = ((inv_np/ 
                    components['Inv']['eta'])/ 
                    components['ModCol']['eta'])
    POI_lim_PV_p = (POI/ 
                    arr_to_POI_temp)
    PCS_lim_charge_p = (PCS_np* 
                        components['BattCol']['eta'])
    PCS_lim_charge_p = np.full([array_length], PCS_lim_charge_p)    # Constant value, repeated to length.
    PCS_lim_disch_p = (PCS_np/ 
                        components['BattCol']['eta']/ 
                        components['PCS']['eta'])
    PCS_lim_disch_p = np.full([array_length], PCS_lim_disch_p)      # Constant value, repeated to length.
    # Battery charge power limited by C rate, and PCS rating
    batt_charge_p = np.clip(batt_power['max p'], 0, PCS_lim_charge_p)
    # Battery discharge power limited by C rate and PCS rating 
    batt_disch_p = np.clip(batt_power['max p'], 0, PCS_lim_disch_p)
    # Power limited by battery
    # TODO: line throws a runtime error for division by zero in the case that augmentation is not used,
    # leading to battery charge power and charge eta not existing for the hours past battery life span
    batt_lim_denom = np.divide(arr_to_batt, batt_power['charge eta'], out=np.zeros_like(arr_to_batt), where=batt_power['charge eta']!=0)
    batt_lim_PV_p = np.divide(batt_charge_p, batt_lim_denom, out=np.zeros_like(batt_charge_p), where=batt_lim_denom!=0)
    
    # array energy limited by PV energy and inverter rating 
    inv_lim_PV_e = np.clip(PV_energy, 0, inv_lim_PV_p)
    # inv_lim_PV_e = PV_energy
    # Array energy limited by PV energy and POI rating 
    POI_lim_PV_e = np.clip(PV_energy, 0, POI_lim_PV_p)
   
    # Compile into output dictionary
    limits_dict = {'inverter limit PV power': inv_lim_PV_p,
                   'POI limit PV power': POI_lim_PV_p,
                   'PCS limit battery charge power': PCS_lim_charge_p,
                   'PCS limit battery discharge power': PCS_lim_disch_p,
                   'battery charge power': batt_charge_p,
                   'battery discharge power': batt_disch_p,
                   'power limited by battery': batt_lim_PV_p,
                   'array energy inverter limited': inv_lim_PV_e,
                   'array energy POI limited': POI_lim_PV_e}
    
    return loss_dict, limits_dict
