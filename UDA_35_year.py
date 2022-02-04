# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 08:26:11 2021
Project configuration, test of setup paramaters and how to call

@author: Derek Ackerman
"""
#%% Imports
import pandas as pd
import numpy as np
import time
import os
import datetime as dt
import configuration              # project configuration, pulls from database
import functions as fun           # functions library
# import battery_functions as batt  # Battery functions, degradation, and hourly capacity and efficiencies
import monthly_battery_functions as batt
import rate_functions as rate     # Suite of rate functions, simpler interface for one-off
import pvs as dispatch          # medium voltage AC arbitrage function
# import plot_tools as plotit
import timearray_gen
import gc                         # python garbage collector

#%% Project Declarations
plant_name = 'UDA'           # name of project
utility = 'Montana'         # offtaking utility
POI = 80                       # interconnection (MW)
months_pre_construction = 25    # construction timing
months_construction = 6
months_pre_COD = 1
years_PPA = 12                  # PPA contract length
date_COD = dt.date(2023,1,1)    # Commercial operation date
date_start = date_COD - dt.timedelta(days=30*(months_pre_construction+months_construction+months_pre_COD))
file_name = 'UDA_1.2.csv'           # name of pv syst output file

battery_limit_at_POI = 40
battery_hours_at_POI = 4
#%% Equipment selection
"""
equipment selection call formatted as follows:
    
module, module collector, inverter, inverter medium voltage collector, inverter 
medium voltage trasformer, battery, battery collector, PCS, PCS medium voltage 
collector, PCS medium voltage transformer, GSU

the modules, inverters, batteries and PCS are called based on model name, other 
components will be stored using the project name if applicable
"""
module = 'Waaree_535'
inverter = 'chint_275'
battery = 'catl_atrisco'
PCS = 'sungrow_sc3450'

# pull all component dictionaries 
component_dict = configuration.config_project(mod_name=module,
                                                inv_name=inverter,
                                                batt_name=battery,
                                                pcs_name=PCS)

 
component_dict['ModCol']['eta'] = 1
#%% Import 8760
start = time.time()
array_dict = fun.populate_8760(file_name)
print(f'PV-Syst file retrieval time: {time.time()-start} seconds')
# Replicate 1 year array energy over life span of installed modules
array_life = np.tile(array_dict['array energy'], component_dict['Mod']['life'])
start = time.time()

#%% Calculate module degradation
module_deg = fun.module_degradation(component_dict['Mod'])

#%% populate battery system
""" 
Version 1 will not include augmentation scheduling and size selection, attempting
to keep selection modular so that implementation is simple

first thoughts are that augmentation schedule will be a list, of dictionaries 
keyed for year, and size(MWh), including initial construction
"""
batt_deg = batt.battery_degradation(component_dict['Batt'], 1)

#%% Parameter slider declarations
dc_ac = [1.20,1.20,0.05] 
inv_np = [1.1275*POI, 1.1275*POI,.05*POI]
# PCS_np = [300/0.9474488182451114, 400/0.9474488182451114, 25/0.9474488182451114]
PCS_np = [237.2, 237.2, 100]
batt_hour = [1.0, 1.0, 1.0]
aug_sched = [[0,189.8],[4,14.6],[8,14.6],[13,14.6],[17,14.6],[21,146],[24,29.2],[28,36.5]]

#%% Define minimum charge threshold (%) and the min PPA difference
PV_min_energy_chg_threshold = 0.10  # Percent of daily maximum array energy
                                    # needed to charge battery
ppa_min_delta = 8

#%% define rate data for the run
# for initial run using desired discharge periods in place of true rate data, 
# constructing a function to read standardized inputs from development team

project_rates = rate.uda_35()

print(f'time through loading rates: {time.time()-start} seconds\n')

#%% define cases, populate case list
case_list = fun.define_cases(component_dict,
                             module_deg, 
                             array_life,
                             batt_deg,
                             POI, 
                             dc_ac, 
                             inv_np,
                             PCS_np, 
                             batt_hour,
                             aug_sched) 

#%% Dispatch
dispatch.arbitrage(PV_min_energy_chg_threshold, ppa_min_delta, case_list, project_rates, battery_limit_at_POI, battery_hours_at_POI)

#%% plotting
date_time_out = timearray_gen.time_array(date_start,
                date_COD,
                months_pre_construction,
                months_construction,
                months_pre_COD,
                years_PPA,
                component_dict['Mod']['life'])

year_1 = case_list['Case 1']['dispatch output']

print('\n\n')
import matplotlib.pyplot as plt
python_PVS = year_1['PVS POI output - PV'] + year_1['PVS POI output - battery']
python_PV = year_1['PV only plant energy']
plt.figure(1)
plt.plot_date(date_time_out, python_PVS, linestyle='-')
plt.plot_date(date_time_out, python_PV, linestyle='-')
plt.title('PVS output vs PV only')
plt.legend(['PVS output','PV only output'])


clip_out = python_PV + year_1['clip harvesting']
plt.figure(2)
plt.plot_date(date_time_out, year_1['inverter output'], linestyle='-')
plt.plot_date(date_time_out, python_PV, linestyle='-')
plt.plot_date(date_time_out, clip_out, linestyle='-')
plt.legend(['Inverter out','PV output','PV out + clip harvesting'])
plt.title('inverter output pre and post POI clipping')    

plt.figure(3)
plt.plot_date(date_time_out, year_1['PVS POI output - battery'], linestyle='-')
plt.legend('battery output')

plt.figure(4)
plt.plot_date(date_time_out,case_list['Case 1']['battery capacity']['capacity'], linestyle='-')

POI_cap_batt = []
RTE_annual = []
for i in range(0,35):
    POI_cap_batt.append(case_list['Case 1']['battery power']['DOD np'][8760*i+8759]*
                        case_list['Case 1']['losses']['battery to POI'][8760*i+8759]/4)
    RTE_annual.append(case_list['Case 1']['battery capacity']['rte'][8760*i+8759])
    
# import matplotlib.pyplot as plt
plt.figure(1)
plt.plot(POI_cap_batt)
plt.figure(2)
plt.plot(RTE_annual)
plt.figure(3)
plt.plot(year_1["PVS POI output - battery"])
print(f'PVS output: {python_PVS[:8760].sum()}\nPV only: {python_PV[:8760].sum()}\n\n')
print(f'battery max at POI: {year_1["PVS POI output - battery"].max()}\n')
#%% Calculate financial difference PV_only vs PV+ESS
PV_financial = np.zeros((len(python_PV)))
PVS_financial = np.zeros((len(python_PVS)))
pv_financial = python_PV*project_rates['rate combined']
pvs_financial = python_PVS*project_rates['rate combined']


df_output = pd.DataFrame(index=date_time_out)
df_output['PV only energy at POI (MWh)'] = python_PV
df_output['PV only * WoodMac & Ventyx ($)'] = pv_financial
df_output['PV + S energy at POI (MWh)'] = python_PVS
df_output['PV + S * WoodMac & Ventyx ($)'] = pvs_financial
df_output['WoodMac & Ventyx ($)'] = project_rates['rate combined']
df_output['WoodMac ($)'] = project_rates['rate energy']
df_output['Ventyx ($)'] = project_rates['rate capacity']
df_output['battery capacity at POI (MWh)'] = (case_list['Case 1']['battery power']['DOD np']*
                                        case_list['Case 1']['losses']['battery to POI'])
df_output['battery discharge at POI'] = year_1['PVS POI output - battery']
df_output['battery capacity installed (DOD_np) (MWh)'] = case_list['Case 1']['battery power']['DOD np']
df_output['battery SOC (%)'] = case_list['Case 1']['dispatch output']['battery SOC %']
df_output['battery SOC (MWh)'] = case_list['Case 1']['dispatch output']['battery SOC MWh']

df_temp_1 = pd.DataFrame(index=date_time_out)
df_temp_1['PV only energy at POI (MWh)'] = python_PV
df_temp_1['PV only * WoodMac & Ventyx ($)'] = pv_financial
df_temp_1['PV + S energy at POI (MWh)'] = python_PVS
df_temp_1['PV + S * WoodMac & Ventyx ($)'] = pvs_financial

df_temp_2 = pd.DataFrame(index=date_time_out)
df_temp_2['WoodMac & Ventyx ($)'] = project_rates['rate combined']
df_temp_2['WoodMac ($)'] = project_rates['rate energy']
df_temp_2['Ventyx ($)'] = project_rates['rate capacity']
df_temp_2 = df_temp_2.multiply(python_PVS, axis=0)

df_temp_3 = pd.DataFrame(index=date_time_out)
df_temp_3['battery capacity at POI (MWh)'] = (case_list['Case 1']['battery power']['DOD np']*
                                        case_list['Case 1']['losses']['battery to POI'])
df_temp_3['battery capacity installed (DOD_np) (MWh)'] = case_list['Case 1']['battery power']['DOD np']
df_temp_3['battery SOC (%)'] = case_list['Case 1']['dispatch output']['battery SOC %']
df_temp_3['battery SOC (MWh)'] = case_list['Case 1']['dispatch output']['battery SOC MWh']

df_month_1 = df_temp_1.groupby(pd.Grouper(level=0, freq='1M')).sum()
df_month_2 = df_temp_2.groupby(pd.Grouper(level=0, freq='1M')).sum()
df_month_2 = df_month_2.divide(df_month_1['PV + S energy at POI (MWh)'], axis=0)
df_month = pd.concat([df_month_1, df_month_2], axis=1, join='inner')

df_year_1 = df_temp_1.groupby(pd.Grouper(level=0, freq='1Y')).sum()
# df_year_2 = df_temp_2.groupby(pd.Grouper(level=0, freq='1Y')).mean()
# df_year = pd.concat([df_year_1, df_year_2], axis=1, join='inner')
df_year = df_year_1
# #%% work through each month and calculate the weighted average for pricing 
# annual_weight_ventyx = []
# annual_weight_wood = []
# annual_weight_combo = []

# for i in range(0,35):
#     weight_values = python_PVS[i*8760:(i+1)*8760]
#     ventyx_temp = project_rates['rate capacity'][i*8760:(i+1)*8760]
#     woodmac_temp = project_rates['rate energy'][i*8760:(i+1)*8760]
#     combo_temp = project_rates['rate combined'][i*8760:(i+1)*8760]
#     annual_weight_ventyx.append((ventyx_temp*weight_values).sum()/weight_values.sum())
#     annual_weight_wood.append((woodmac_temp*weight_values).sum()/weight_values.sum())
#     annual_weight_combo.append((combo_temp*weight_values).sum()/weight_values.sum())
# df_year['Ventyx ($)'] = annual_weight_ventyx
# df_year['WoodMac ($)'] = annual_weight_wood
# df_year['WoodMac & Ventyx ($)'] = annual_weight_combo

# loc='C:/Users/Derek Ackerman/Documents/Python_ESS/UDA_35_year.xlsx' 
# writer=pd.ExcelWriter(loc)
# df_output.to_excel(writer, sheet_name='35_year hourly')
# df_year.to_excel(writer, sheet_name='35_year_annual')
# df_month.to_excel(writer,sheet_name='35_year_monthly')
# writer.save()
# writer.close()
# # import matplotlib.pyplot as plt
# plt.figure(5)
# plt.plot_date(date_time_out,case_list['Case 1']['dispatch output']['battery SOC MWh'], linestyle='-')
# # plt.plot_date(date_time_out,case_list['Case 1']['dispatch output']['battery charge state'], linestyle='-')
# plt.legend(['MWH','charge state'])

# batt_over_disch = np.clip(case_list['Case 1']['dispatch output']['battery SOC MWh'], -100, 0)
# plt.figure(6)
# plt.plot_date(date_time_out,batt_over_disch, linestyle='-')

# plt.figure(7)
# plt.plot_date(date_time_out, python_PVS, linestyle='-')
# print(f'minimum battery SOC: {case_list["Case 1"]["dispatch output"]["battery SOC MWh"].min()}\n')

