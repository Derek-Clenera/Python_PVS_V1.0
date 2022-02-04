# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 15:46:22 2021

Function to read database and pull out the pertinent information from the 
component assignments

@author: Derek Ackerman
"""

def config_project(mod_name = "default", mod_col_name = "default", 
                   inv_name = "default", mvcol_inv_name = "default", 
                   mvt_inv_name = "default", batt_name = "default", 
                   batt_col_name = "default", pcs_name = "default", 
                   mvcol_pcs_name = "default", mvt_pcs_name = "default", 
                   gsu_name = "default"):
    """
    Function to read database stored component dictionaries (currently stored as JSON).
    Possible switch to commented YAML, though harder to read / write, conversion would
    be simple. 

    Parameters
    ----------
    mod_name : string, optional
        manufacturer / model of solar modules. The default is "default".
    mod_col_name : string, optional
        module collector. The default is "default".
    inv_name : string, optional
        manufacturer / model of inverters. The default is "default".
    mvcol_inv_name : string, optional
        inverter MV collector. The default is "default".
    mvt_inv_name : string, optional
        inverter MV transformer. The default is "default".
    batt_name : string, optional
        manufacturer / model of the battery cell (not ESS module). The default is "default".
    batt_col_name : string, optional
        battery system collector. The default is "default".
    pcs_name : string, optional
        manufacturer / model of power conditioning system. The default is "default".
    mvcol_pcs_name : string, optional
        battery system MV collector. The default is "default".
    mvt_pcs_name : string, optional
        battery system MV transformer. The default is "default".
    gsu_name : string, optional
        Substation transformer. The default is "default".

    Returns
    -------
    components : dict
        dictionary of all components, keyed by the component type / location
        module : dict
            brand : string  manufacturer
            model : string  model
            life  : int  life expectancy of the module
            degradation  : float    annual degradation of the panels
            reliability : dict  used for Josh's program
        batt : dict
            brand : string  manufacturer
            model : string  model
            life : int  usable life span of the battery cell
            min_v : float  minimum voltage of cell
            np : float  nameplate power of battery cell (MW)
            eta_DOD : float  depth of discharge of cell
            rte_BOL : float  round trip n beginning of life
            rte_EOL : float  round trip n end of life
            deg_c365 : list  degradation annual for 1 cycle per day
            deg_c730 : list  degradation annual for 2 cycles per day 
    """
    
    import json
    import os

    # Pull the component dictionaries from dataase
    script_dir = 'C:\\Users\\Derek Ackerman\\Documents\\Python_ESS_cleaned_up\\Components'  #file path to folder holding JSON files
    # Module specifications
    file_path = os.path.join(script_dir, 'Mod.json')
    Mod_file = open(file_path)
    Mod_dict = json.load(Mod_file)
    # Module collector specifications
    file_path = os.path.join(script_dir, 'ModCol.json')
    ModCol_file = open(file_path,)
    ModCol_dict = json.load(ModCol_file)
    # Inverter specifications
    file_path = os.path.join(script_dir, 'Inv.json')
    Inv_file = open(file_path,)
    Inv_dict = json.load(Inv_file)
    # inverter medium voltage collector
    file_path = os.path.join(script_dir, 'MVCol_Inv.json')
    MVCol_Inv_file = open(file_path,)
    MVCol_Inv_dict = json.load(MVCol_Inv_file)
    # inverter medium voltage transformer
    file_path = os.path.join(script_dir, 'MVT_Inv.json')
    MVT_Inv_file = open(file_path,)
    MVT_Inv_dict = json.load(MVT_Inv_file)
    # Battery specifications
    file_path = os.path.join(script_dir, 'Batt.json')
    Batt_file = open(file_path,)
    Batt_dict = json.load(Batt_file)
    # Battery collector specifications
    file_path = os.path.join(script_dir, 'BattCol.json')
    BattCol_file = open(file_path,)
    BattCol_dict = json.load(BattCol_file)
    # PCS specifications
    file_path = os.path.join(script_dir, 'PCS.json')
    PCS_file = open(file_path,)
    PCS_dict = json.load(PCS_file)
    # PCS medium voltage collector
    file_path = os.path.join(script_dir, 'MVCol_PCS.json')
    MVCol_PCS_file = open(file_path,)
    MVCol_PCS_dict = json.load(MVCol_PCS_file)
    # PCS medium voltage transformer
    file_path = os.path.join(script_dir, 'MVT_PCS.json')
    MVT_PCS_file = open(file_path,)
    MVT_PCS_dict = json.load(MVT_PCS_file)
    # GSU
    file_path = os.path.join(script_dir, 'GSU.json')
    GSU_file = open(file_path,)
    GSU_dict = json.load(GSU_file)
    
    # select component dictionaries
    Mod = Mod_dict[mod_name]      
    ModCol = ModCol_dict[mod_col_name]
    Inv = Inv_dict[inv_name]
    MVCol_Inv = MVCol_Inv_dict[mvcol_inv_name]
    MVT_Inv = MVT_Inv_dict[mvt_inv_name]
    Batt = Batt_dict[batt_name]
    BattCol = BattCol_dict[batt_col_name]
    PCS = PCS_dict[pcs_name]
    MVCol_PCS = MVCol_PCS_dict[mvcol_pcs_name]
    MVT_PCS = MVT_PCS_dict[mvt_pcs_name]
    GSU = GSU_dict[gsu_name]
    
    # compile the components into one dictionary and return
    components = {"Mod": Mod, "ModCol": ModCol, "Inv": Inv, "MVCol_Inv": MVCol_Inv,
                  "MVT_Inv": MVT_Inv, "Batt": Batt, "BattCol": BattCol,
                  "PCS": PCS, "MVCol_PCS": MVCol_PCS, "MVT_PCS": MVT_PCS,
                  "GSU": GSU}
    
    return components
