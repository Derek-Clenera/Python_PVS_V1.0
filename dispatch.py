# -*- coding: utf-8 -*-
def daily_arbitrage(arbitrage,
                    POI,
                    PV_min_energy_chg,
                    ppa_min_delta,
                    batt_limit_POI,
                    batt_hours_POI,
                    daily_array):
    import numpy as np

    """
    Function to take an incoming set of information for PV + S simulation, assign
    losses and limits and create preferential pairs for charging and discharging 
    a storage system ranked using node pricing.

    Parameters
    ----------
    arbitrage : boolean
        boolean check if the rate delta in the day is large enough to prompt
        battery charge / discharge.
    POI : int
        Point of interconnect rating (MW).
    PV_min_energy_chg : float
        Minimum array energy required to start charging the battery.
    ppa_min_delta : float
        Minimum delta between high and low rate pricing to perform arbitrage.
    batt_limit_POI: int
        PCS limit at the POI.
    batt_hours_POI: int
        hours to dispatch at the POI limit.
    daily_array : dict
        Dictionary containing the following information:
              0:      array energy
              1:      capacity rate
              2:      combined rate
              3:      energy rate
              4:      RA rate
              5:      REC rate
              6:      array energy inverter limited
              7:      array energy POI limited
              8:      battery charge power
              9:     battery discharge power
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
              24:     rte (battery)Bat

    Returns
    -------
    pvs_out : dict
        returns a dictionary containing the following information:
            0:      PV only plant energy
            1:      PVS POI output - PV
            2:      PVS POI output - battery
            3:      battery SOC %
            4:      battery SOC MWh
            5:      node meter PVS
            6:      node meter PV
            7:      POI meter PVS
            8:      POI meter PV
            9:      battery charge state
            10:     charge sequence
            11:     discharge sequence
            12:     hour sequence

    """
    pcs_np = batt_limit_POI
    batt_cap_limit = pcs_np*batt_hours_POI
    # populate containers for 24 hour period.
    seq_index_24 = np.arange(0,24,1)        
    seq_chg_24 = np.zeros((24,7))
    seq_disch_24 = np.zeros((24,7))
    seq_chg_matrix = np.zeros((24,14))
    seq_disch_matrix = np.zeros((24,11))
    clip_chglim_batt_e = np.zeros((24))
    clip_batt_e = np.zeros((24))
    clip_stat_batt_chg = np.zeros((24))
    clip_chg_PV_e = np.zeros((24))
    PV_chglim_batt_e = np.zeros((24))
    PV_chg_batt_e = np.zeros((24))
    PV_chg_stat_batt_chg = np.zeros((24))
    PV_chg_PV_e = np.zeros((24))
    disch_lim_batt_e = np.zeros((24))
    disch_batt_e = np.zeros((24))
    disch_POI_e = np.zeros((24))
    stat_batt_disch = np.zeros((24))
    batt_SOC = np.zeros((24))
    seq_chg_sort_index = np.zeros((24,11))
    seq_disch_sort_index = np.zeros((24,11))
    seq_chg_matrix = np.empty((24,14))
    seq_disch_matrix = np.empty((24,11))
    gap_POI_p_24 = np.zeros((24))
    PV_only_POI_e = np.zeros((24))
    deliverable_PV_e = np.zeros((24))
    batt_recap_PV_e = np.zeros((24))
    inv_out_e = np.zeros((24))
    
    # make the non-PV hours rate high for sorting purposes.
    PV_charge_enabled = np.where(daily_array[:,0]>PV_min_energy_chg,True,False)
    PV_charge_enabled = PV_charge_enabled + np.where(PV_charge_enabled==0, 
                                                     1000, 0)
    PV_charge_cost = PV_charge_enabled * daily_array[:,2]
    
    # Step 1: charge battery using clipped energy only.
    for hour in range(0,24):
        # case 1: Inverter limit PV power > POI limit PV power -> POI is limiting .
        if daily_array[hour,10] > daily_array[hour,13]:
            # Deliverable PV energy = minimum value between
            # battery power limit+ array energy POI limited and 
            # array energy inverter limited.
            deliverable_PV_e[hour] = min((daily_array[hour,14]+      
                                         daily_array[hour,7]),  
                                        daily_array[hour,6])
            
            inv_out_e[hour] = daily_array[hour,6]
            
            # PV only output = array energy POI limited * losses array to POI.
            PV_only_POI_e[hour] = (daily_array[hour,7] *
                                   daily_array[hour,17])
            # Recapturable PV energy (clip harvesting) = deliverable PV energy -
            # Array energy POI limited.
            batt_recap_PV_e[hour] = (deliverable_PV_e[hour] - 
                                     daily_array[hour,7])
        else:
        # case 2: inverter limit PV power < POI limit PV pwer -> inverter is limiting.
            # Deliverable PV energy = minimum value between array energy
            # and inverter limit PV power.
            deliverable_PV_e[hour] = min(daily_array[hour,10], daily_array[hour,0])
            # PV only output = deliverable PV energy * losses array to POI.
            PV_only_POI_e[hour] = (deliverable_PV_e[hour] *
                          daily_array[hour,17])
            # No clipping therefore no clip harvesting.
            batt_recap_PV_e[hour] = 0
            inv_out_e[hour] = min(deliverable_PV_e[hour], daily_array[hour,6])
        # Battery clip harvestin charge limit = minimum value between
        # battery charge power * battery charge efficiency, and 
        # clip harvesting amount * losses array to battery.
        clip_chglim_batt_e[hour] = min((daily_array[hour,8]*
                              daily_array[hour,19]),
                             (batt_recap_PV_e[hour]*
                              daily_array[hour,15]))
        # Battery capacity limit = minimum value between
        # clip charge limit from previous comparison and 
        # DOD nameplate - amount charged in the battery over previous hours.
        clip_chglim_batt_e[hour] = min(clip_chglim_batt_e[hour], 
                                       (daily_array[hour,21] -
                                        batt_SOC.sum()),
                                       batt_cap_limit/daily_array[hour,18]-batt_SOC.sum(),
                                       pcs_np/daily_array[hour,15])
        # Check to ensure non-negative values.
        clip_chglim_batt_e[hour] = max(0, clip_chglim_batt_e[hour])
        # Check for room to charge using the total state of charge (MW), vs 
        # DOD nameplate.
        if batt_SOC.sum() < daily_array[hour,21]:
            # Room exists for the day to charge battery.
            # Charge the clipped energy.
            batt_SOC[hour] = batt_SOC[hour] + clip_chglim_batt_e[hour]
            # Clip harvested energy = clipped energy in the battery / 
            # losses array to the battery.
            clip_chg_PV_e[hour] = clip_chglim_batt_e[hour] / daily_array[hour,15]
            # Update tracking of clip harvesting and set boolean flag to True for the hour. 
            clip_batt_e[hour] = clip_chglim_batt_e[hour]
            clip_stat_batt_chg[hour] = True
        else:
            # no room to charge the battery
            clip_chg_PV_e[hour] = 0
            clip_batt_e[hour] = 0
            clip_stat_batt_chg[hour] = False
            # Check flag state to ensure charge actually was increased during a flagged hour.
        clip_stat_batt_chg[hour] = (clip_stat_batt_chg[hour] and 
                                    (batt_recap_PV_e[hour] > 0))
        
    # Build daily charge array for sorting later
    seq_chg_24[:,0] = seq_index_24          # 24 hour sequence 0-23.
    seq_chg_24[:,1] = daily_array[:,0]      # Array energy.
    seq_chg_24[:,2] = PV_charge_cost        # charge cost with non-available hours set high.
    seq_chg_24[:,3] = clip_stat_batt_chg    # charge state flags.
    seq_chg_24[:,4] = clip_batt_e           # clipped energy charged into the battery.
    seq_chg_24[:,5] = deliverable_PV_e      # PV energy deliverable with limits in place.
    seq_chg_24[:,6] = clip_chg_PV_e         # PV energy pre losses charged to the battery.
    # Determine charge hours after the array rearrangement.
    # sort by cost to charge, then by hour, which should ensure that hours with more available PV energy are charged with priority
    sort_indexing = np.lexsort((seq_chg_24[:,0], seq_chg_24[:,2]))  
    # Sort the charge output by PV charge cost (ascending), and break ties
    # by 24 hour sequence (aschending).
    seq_chg_sort_24 = seq_chg_24[sort_indexing,:]
    
    # Step 2: charge battery from remaining PV energy after the clip.
    for hour in range(0,24):
        # Set a reference hour for loss / limits.
        ref_hour = int(seq_chg_sort_24[hour,0])
        # array energy charge limit to the battery = minimum value between
        # battery charge power * charge efficiency,
        # deliverable PV energy * array to battery losses - clipped energy 
        # harvested during the hour. 
        PV_chglim_batt_e[hour] = (min((daily_array[ref_hour,8]*
                                      daily_array[ref_hour,19]),
                                      (seq_chg_sort_24[hour,5]*
                                       daily_array[ref_hour,15]))-
                                      seq_chg_sort_24[hour,4])
        # Battery capacity limit = minimum value between
        # previous charge limit and DOD nameplate - daily charge accrued. 
        PV_chglim_batt_e[hour] = min(PV_chglim_batt_e[hour],
                                     (daily_array[ref_hour,21] -
                                      batt_SOC.sum()),
                                     batt_cap_limit/daily_array[ref_hour,18]-batt_SOC.sum(),
                                     pcs_np/daily_array[ref_hour,15])
        # Check to ensure non-negative values.
        PV_chglim_batt_e[hour] = max(0, PV_chglim_batt_e[hour])
        # Perform charge if in an arbitrage situation. 
        if ((batt_SOC.sum() < daily_array[ref_hour,21]) and arbitrage):
            # Room to charge battery.
            # Battery SOC for the hour is updated with the charge limit energy.
            batt_SOC[ref_hour] = (batt_SOC[ref_hour]+ 
                                  PV_chglim_batt_e[hour])
            # Array energy used to charge the battery =
            # energy charged in the battery / losses array to battery.
            PV_chg_PV_e[hour] = (PV_chglim_batt_e[hour]/
                                 daily_array[ref_hour,15])
            # PV charged to battery is updated with the amount charged to the battery, 
            # and the flag is set to true. 
            PV_chg_batt_e[hour] = PV_chglim_batt_e[hour]
            PV_chg_stat_batt_chg[hour] = True
        else:
            # No room to charge the battery.
            PV_chg_PV_e[hour] = 0
            PV_chg_batt_e[hour] = 0
            PV_chg_stat_batt_chg[hour] = False
    
    # Create array for sorting.
    seq_chg_sort_index[:, 0:7] = seq_chg_sort_24    # Values from clip harvesting.
    seq_chg_sort_index[:,7] = seq_index_24          # 24 hour sequence (0-23).
    seq_chg_sort_index[:,8] = PV_chg_stat_batt_chg  # Boolean state for charging.
    seq_chg_sort_index[:,9] = PV_chg_batt_e         # Energy charged in the battery.
    seq_chg_sort_index[:,10] = PV_chg_PV_e          # Array energy used to charge the battery.
    
    # Rearrange back to original 24 hour order. 
    # Sort by original 24 hour sequence (ascending).
    seq_chg_sort_new = seq_chg_sort_index[seq_chg_sort_index[:,0].argsort()]
    # Charge in the battery = charge from clipping + charge from PV.
    chg_batt_e_24 = seq_chg_sort_new[:,4] + seq_chg_sort_new[:,9]
    # Array energy used to charge the battery = array energy clipped and harvested 
    # + array energy used to charge. 
    chg_PV_e_24 = seq_chg_sort_new[:,6] + seq_chg_sort_new[:,10]
    # Array energy allowed to pass through to the POI / not used for charging =
    # the minimum between deliverable array energy - array energy charged to the battery *
    # losses array to POI.
    PV_less_chg_POI_e_24 = (np.minimum((deliverable_PV_e - chg_PV_e_24),daily_array[:,7])
                            *daily_array[:,17])
    # Populate the new charge array.
    seq_chg_matrix[:,0:11] = seq_chg_sort_new       # Values from original charge sequence array.
    seq_chg_matrix[:,11] = chg_batt_e_24            # Charge in the battery.
    seq_chg_matrix[:,12] = chg_PV_e_24              # Array energy used to charge the battery.
    seq_chg_matrix[:,13] = PV_less_chg_POI_e_24     # Array energy passed to POI.
    
    # Determine daily hours for discharge based on energy rate and battery size.
    # Build daily discharge array for sorting later.
    seq_disch_24[:,0] = seq_index_24                # 24 hour sequence (0-23).
    seq_disch_24[:,1] = daily_array[:,0]            # Array energy.
    seq_disch_24[:,2] = daily_array[:,2]            # Combined rate.
    seq_disch_24[:,3] = np.zeros([24])              # Unused variable, in matlab is inverter limited PV_energy.
    seq_disch_24[:,4] = seq_chg_sort_new[:,5]       # Deliverable PV energy.
    seq_disch_24[:,5] = chg_PV_e_24                 # Array energy used to charge the battery.
    seq_disch_24[:,6] = PV_less_chg_POI_e_24        # Array energy allowed to pass to the POI.
    
    # Determine how to sequence the discharge hours.
    if arbitrage:
    # If in an arbitrage day due to rate delta.
        # Sort discharge array by combined rate (ascending), tie-break using 24 hour sequence.
        sort_indexing = np.lexsort((seq_disch_24[:,0], seq_disch_24[:,2]))
        seq_disch_sort_24 = seq_disch_24[sort_indexing]
    else:
    # If not in an arbitrage day due to rate delta.
        seq_disch_sort_24 = seq_disch_24
    
    # Step 3: Battery discharge
    for hour in range(23,-1,-1):
        # Determine reference hour for loss assignments and limits.
        ref_hour = int(seq_disch_sort_24[hour,0])
        # Battery discharge limit = minimum value between 
        # Battery discharge power limit and 
        # remaining SOC (MWh) * battery discharge efficiency.
        disch_lim_batt_e[hour] = min(daily_array[ref_hour,9],
                                    (batt_SOC.sum()),
                                    batt_cap_limit*daily_array[ref_hour,20],
                                    pcs_np/daily_array[ref_hour,18]) 
        # Gap to POI = POI - array energy allowed to pass to the POI
        # TODO: Possible update to not use PV less charge to avoid scenarios where 
        # there is a charge and discharge flag at the same time (not likely).
        gap_POI_p_24[hour] = POI - seq_disch_sort_24[hour,6]
        # Check for depth of discharge performed to suppress warnings
        # when dividing by zero, appears to have no impact on speed.
        if (daily_array[ref_hour, 21] > 0):
        # If the battery system still has a DOD nameplate > 0
            # Battery discharge limit = minimum value between
            # existing discharge limit, POI gap / losses discharge effiency and 
            # battery to POI.
            disch_lim_batt_e[hour] = min(disch_lim_batt_e[hour],
                                      (gap_POI_p_24[hour]/
                                      daily_array[ref_hour,18]))
                                      # *daily_array[ref_hour,20])
        else:
        # Battery is past end of life.
            disch_lim_batt_e[hour] = 0
        # ensure non negative values
        disch_lim_batt_e[hour] = max(0, disch_lim_batt_e[hour])
        
        if (batt_SOC.sum() > 0):
        # If there is charge left in the battery 
            # Set a temporary SOC for the desired discharge hour
            temp_soc = 0.0
            temp_hour = ref_hour
            current_discharge_limit = disch_lim_batt_e[hour]
            # While there is time between the start of the day and the hour 
            # discharging is desired, continue to add to available capacity.
            while temp_hour >=0 and temp_soc < current_discharge_limit:
                # If taking all of the available capacity in the battery at that hour
                # will be less than the discharge limit, take all of it.
                if ((temp_soc + batt_SOC[temp_hour]) < current_discharge_limit):
                    temp_soc += batt_SOC[temp_hour]
                    batt_SOC[temp_hour] = 0
                # If there is still room to meet the desired discharge for 
                # the hour but not all that's available then:
                elif (temp_soc < current_discharge_limit):
                    # establish the difference, and how much is available
                    diff_remain = disch_lim_batt_e[hour] - temp_soc
                    avail_charge = batt_SOC[temp_hour]
                    # If there is anything to count towards the dicharging hour:
                    if ((avail_charge > 0) and ((avail_charge - diff_remain) > 0)):
                        # Add the difference to the discharge hour.
                        temp_soc += diff_remain
                        # Update the battery SOC by the amount scheduled for discharge
                        batt_SOC[temp_hour] = avail_charge - diff_remain
                    # TODO: Archaic logic, might not be necessary
                    else:
                        temp_soc += batt_SOC[temp_hour]
                        batt_SOC[temp_hour] = 0
                temp_hour -=1
                
            # Update the battery discharge for the hour by the available SOC from 
            # predceeding hours
            disch_batt_e[hour] = temp_soc
            # Discharge to the POI for the hour is the alloted charge times
            # losses battery to POI.
            disch_POI_e[hour] = (temp_soc*
                                  daily_array[ref_hour,18])
            if temp_soc > 0:
                stat_batt_disch[hour] = True                    
            
        else:
        # No charge left in the battery.
            disch_batt_e[hour] = 0
            disch_POI_e[hour] = 0
            stat_batt_disch[hour] = False
        
    # Collect the discharge information and sort to original 24 hour order
    seq_disch_sort_index[:,0:7] = seq_disch_sort_24     # Original values from discharge array.
    seq_disch_sort_index[:,7] = seq_index_24            # 24 hour index (0-23).
    seq_disch_sort_index[:,8] = stat_batt_disch         # Boolean flag for discharging
    seq_disch_sort_index[:,9] = disch_batt_e            # Energy discharged from the battery.
    seq_disch_sort_index[:,10] = disch_POI_e            # Energy discharged from the battery as seen at POI.
    # Sort the discharge array by the original 24 hour index.
    seq_disch_sort_new = seq_disch_sort_index[seq_disch_sort_index[:,0].argsort()]
    seq_disch_matrix = seq_disch_sort_new
    
    # Determine the charge and discharge schedule
    clip_stat_batt_chg = seq_chg_matrix[:,3]            # Boolean state for charging the battery using clip harvesting.
    PV_chg_stat_batt_chg = seq_chg_matrix[:,8]          # Boolean state for charging the battery outside clip harvesting.
    stat_batt_disch = seq_disch_matrix[:,8]             # Boolean state for discharging the battery.
    chg_seq = seq_chg_matrix[:,7]                       # 24 hour index sorted for charging.
    disch_seq = seq_disch_matrix[:,7]                   # 24 hour index sorted for discharging.
    chg_batt_e = seq_chg_matrix[:,11]                   # Battery charge.
    # TODO: the expanded division is used to bypass periods where the battery system 
    # is past life, avoids division by zero errors. Not necessary with augmentation. 
    chg_PV_e = np.divide(chg_batt_e,                    # array energy used to charge the battery = energy charged in the battery by PV / 
                         daily_array[:,15],             # losses array to battery.
                         out=np.zeros_like(chg_batt_e), 
                         where=daily_array[:,15]!=0)
    disch_batt_e = seq_disch_matrix[:,9]                # Energy discharged from the battery.
    batt_e = -chg_batt_e + disch_batt_e                 # Battery energy = - charged energy and + discharged energy by hour.
    PV_less_chg_POI_e = seq_chg_matrix[:,13]            # Array energy passed to the POI.
    disch_POI_e = seq_disch_matrix[:,10]                # Battery discharge at POI.
    POI_e = PV_less_chg_POI_e + disch_POI_e             # POI output 
    
    # Find the state of charge for the battery 
    batt_SOC_tmp = 0
    batt_SOC_pct = np.zeros([24])
    batt_SOC_MWh = np.zeros([24])
    for i in range(0,24,1):
        # Temporary state of charge equals existing SOC - battery charge / discharge for the given hour.
        batt_SOC_tmp = batt_SOC_tmp - batt_e[i]
        batt_SOC_MWh[i] = batt_SOC_tmp
        # DOD nameplate = DOD nameplate.
        # TODO: This check is another point to avoid division by zero past the point of the battery system end of life.
        dod_np_tmp = daily_array[i,21]
        if dod_np_tmp != 0:
            batt_SOC_pct[i] = batt_SOC_tmp / dod_np_tmp
        else:
            batt_SOC_pct[i] = 0
        
    # Remove rounding errors from battery SOC
    batt_SOC_pct = np.round(batt_SOC_pct,8)
    batt_SOC_MWh = np.round(batt_SOC_MWh,8)
    batt_SOC_pct[np.where(batt_SOC_pct == -0)] = 0
    batt_SOC_MWh[np.where(batt_SOC_MWh == -0)] = 0
    # Array energy delivered = PV not used to charge the battery / losses array to POI
    # plus the array energy used to charge the battery (pre-losses).
    delivered_PV_e = (PV_less_chg_POI_e / daily_array[:,17]) + chg_PV_e
    # Array energy exceeding POI and charge ability = array energy - delivered array energy.
    waste_PV_e = daily_array[:,0] - delivered_PV_e
    node_meter_PVS_e = delivered_PV_e * daily_array[:,16]
    node_meter_PV_e = (PV_only_POI_e/
                       daily_array[:,17]*
                       daily_array[:,16])
    POI_meter_PVS_e = delivered_PV_e * daily_array[:,17]
    POI_meter_PV_e = PV_only_POI_e
    PV_only_wasted_energy = daily_array[:,0] - PV_only_POI_e / daily_array[:,17]
    
    # pv_only_inv_out = PV_only_POI_e / daily_array[:,17]
    # pv_only_inv_out = daily_array[:,6]
    # pv_only_inv_out = PV_only_POI_e + batt_recap_PV_e
    pv_only_inv_out = inv_out_e
    clip_harvesting = clip_chglim_batt_e
    
    """ The current matlab code only makes use of several of these calculated outputs.
        For revision 1, those are the ones returned from the dispatch function """
    # Format output into 24 hour array for storage.
    pvs_out = np.empty([24,15])
    pvs_out[:,0] = PV_only_POI_e
    pvs_out[:,1] = PV_less_chg_POI_e
    pvs_out[:,2] = disch_POI_e
    pvs_out[:,3] = batt_SOC_pct
    pvs_out[:,4] = batt_SOC_MWh
    pvs_out[:,5] = node_meter_PVS_e
    pvs_out[:,6] = node_meter_PV_e
    pvs_out[:,7] = POI_meter_PVS_e
    pvs_out[:,8] = POI_meter_PV_e
    pvs_out[:,9] = batt_e
    pvs_out[:,10] = chg_seq
    pvs_out[:,11] = disch_seq
    pvs_out[:,12] = seq_index_24
    pvs_out[:,13] = pv_only_inv_out
    pvs_out[:,14] = clip_harvesting
            
    return pvs_out
