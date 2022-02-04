# -*- coding: utf-8 -*-
"""
Set of functions to take rate data and convert it to hourly values over the life
of a project, in future revisions running to end of PPA would be ideal, once a 
module for merchant period is designed and tested 

Created on Tue Sep 14 08:37:41 2021

@author: Derek Ackerman
"""

def simple_rates(rate_years,
                 daily_rates):
    """
    Function to create a rate data dictionary for cases that are only interested in 
    storage and dispatch behavior, not for financial modeling. 

    Inputs:
        rate_years  int     number of years to create hourly data *Note, in future,
                            using PPA length for population of 
                            hourly array is preferable
        daily_rates list    24 hour rate data with high values for desired dispatch windows 
                            and low values for unnecessary periods

    Outputs:
        rate_dict   dictionary  dictionary of hourly data * module life for the site
                energy rate     
                capacity rate
                REC rate
                RA rate
                combined rate
    """
    import numpy as np
    # Check if you have been given a full days worth of rate data
    if(len(daily_rates) != 24):
        return('rate data not the correct length')
    # Update combined rates with the passed list, for the number of years the project is active
    rate_comb = np.tile(daily_rates,365*rate_years)
    rate_e = np.zeros(len(rate_comb))               # set the currently unused rate data to zeros
    rate_cap = rate_e
    rate_rec = rate_e
    rate_ra = rate_e
    rate_dict = {'rate energy': rate_e,
                 'rate capacity': rate_cap,
                 'rate REC': rate_rec,
                 'rate RA': rate_ra,
                 'rate combined': rate_comb}
    return rate_dict

def cedar_island_rates(rate_years):
    """
    Function to create specific rate data for Cedar Island

    Parameters
    ----------
    rate_years : TYPE
        DESCRIPTION.

    Returns
    -------
    rate_dict : TYPE
        DESCRIPTION.

    """
    import numpy as np
    # Create load requirement rates for Cedar Island PGE simulation
    jan =       [  5,  5,  5,  5,  5,  5,
                  30, 50, 70, 50, 30, 20,
                  10, 10, 10, 10, 50, 60,
                  90, 80, 70, 40, 10, 10]
    feb =       [  5,  5,  5,  5,  5,  5,
                  10, 30, 30, 10, 10, 10,
                  10, 10, 10, 10, 10, 20,
                  30, 30, 20, 20, 10,  5]
    mar =       [  5,  5,  5,  5,  5,  5,
                  10, 10, 10,  5,  5,  5,
                   5,  5,  5,  5,  5, 10,
                  10, 10,  5,  5,  5,  5]
    # apr =       [  5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5]
    apr =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5, 10, 10,
                  10, 10, 10,  5,  5,  5]
    may =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5, 10, 10, 10,
                  10, 10, 10,  5,  5,  5]
    jun =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                  10, 10, 10, 10, 10, 10,
                  10, 10, 10, 10,  5,  5]
    jul =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5, 10,
                  10, 10, 10, 10, 20, 20,
                  30, 30, 20, 10,  5,  5]
    aug =       [  5,  5,  5,  5,  5,  5, 
                   5,  5,  5,  5, 10, 10,
                  10, 20, 40, 10, 20, 40,
                  60, 40, 60, 20,  5,  5]
    sep =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5, 10,
                  10, 10, 10, 10, 20, 20,
                  30, 30, 20, 10,  5,  5]
    # october =   [  5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5,
    #                5,  5,  5,  5,  5,  5]
    october =   [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5, 10, 10,
                  10, 10, 10,  5,  5,  5]
    nov =       [  5,  5,  5,  5,  5,  5,
                  10, 10, 10, 10, 10, 10,
                  10, 10, 10, 10, 10, 10,
                  20, 20, 10, 10,  5,  5]
    dec =       [  5,  5,  5,  5,  5,  5,
                  30, 50, 50, 30, 20, 20,
                  20, 20, 20, 20, 50, 40,
                  50, 40, 30, 20,  5,  5]

    month_rates = [jan,feb,mar,apr,may,jun,jul,aug,sep,october,nov,dec]
    month_days = [31,28,31,30,31,30,31,31,30,31,30,31]
    # populate rate energy for 1 year
    rate_energy_temp = []
    for i in range(len(month_days)):
        months_rate = month_rates[i]
        for days in range(month_days[i]):
            rate_energy_temp = rate_energy_temp + months_rate

    rate_energy_H = np.tile(rate_energy_temp,rate_years)
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict


def pse_load_rates(rate_years):
    import os
    import pandas as pd
    import numpy as np
    
    # set working directory for the PV-Syst file
    file_name = 'PSE_Load_Hourly.xlsx'
    script_dir = 'C:\\Users\\Derek Ackerman\\Documents\\Battery_test_scripts\\'
    df_overall = pd.read_excel(os.path.join(script_dir, file_name))
    df_temp = df_overall[8760*3+24:8760*4+24]['Unnamed: 2']
    df_8760 = df_temp.to_numpy()

    df_norm = df_8760 / df_8760.min()
    df_norm = df_norm * 100
    rate_energy_temp = df_norm
    rate_energy_H = np.tile(rate_energy_temp,rate_years)
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict
    
    
    
def matlab_rates():
    import numpy as np
    import scipy.io

    rates = scipy.io.loadmat('green_desert_rates')
    # rates = scipy.io.loadmat('green_desert_rates')
    rates = np.squeeze(rates['rate_energy_H'])
    if len(rates) > 306600:
        rates = rates[:306600]
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rates}
    return rate_dict

def cobar_rates(rate_years):
    import numpy as np
    
    jan =       [  5,  5,  5,  5,  5,  5,
                  20, 20, 20,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                  20, 20, 20, 20, 20,  5]
    feb =       [  5,  5,  5,  5,  5,  5,
                  20, 20, 20,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                  20, 20, 20, 20, 20,  5]
    mar =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5]
    apr =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5]
    may =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5]
    jun =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5, 20, 20, 50, 50, 50,
                  50, 50, 50, 20,  5,  5 ]
    jul =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5, 20, 20, 50, 50, 50,
                  50, 50, 50, 20,  5,  5 ]
    aug =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5, 20, 20, 50, 50, 50,
                  50, 50, 50, 20,  5,  5 ]    
    sep =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5, 20, 20, 50, 50, 50,
                  50, 50, 50, 20,  5,  5 ]
    october =   [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5]
    nov =       [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5]    
    dec =       [  5,  5,  5,  5,  5,  5,
                  20, 20, 20,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                  20, 20, 20, 20, 20,  5]
    month_rates = [jan,feb,mar,apr,may,jun,jul,aug,sep,october,nov,dec]
    month_days = [31,28,31,30,31,30,31,31,30,31,30,31]
    # populate rate energy for 1 year
    rate_energy_temp = []
    for i in range(len(month_days)):
        months_rate = month_rates[i]
        for days in range(month_days[i]):
            rate_energy_temp = rate_energy_temp + months_rate
    # Tile output for number of years the panels are active.
    rate_energy_H = np.tile(rate_energy_temp,rate_years)
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict
    
def atrisco_35():
    import os
    import pandas as pd
    import numpy as np
    
    # set working directory for the PV-Syst file
    file_name = 'atrisco_35.csv'
    script_dir = 'C:\\Users\\Derek Ackerman\\Documents\\python_ESS\\'
    df_overall = pd.read_csv(os.path.join(script_dir, file_name),
                               encoding = "ISO-8859-1", 
                               engine='python',header=[0])
    df_temp = df_overall['WoodMac & Ventyx']
    rate_energy_H = df_temp.to_numpy()

    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict

def uda_35():
    import os
    import pandas as pd
    import numpy as np
    
    # set working directory for the PV-Syst file
    file_name = 'UDA_2023.csv'
    script_dir = 'C:\\Users\\Derek Ackerman\\Documents\\python_ESS\\'
    df_overall = pd.read_csv(os.path.join(script_dir, file_name))
                                # encoding = "ISO-8859-1", 
                                # engine='python', header=[0])

    df_temp = df_overall['WoodMac & Ventyx']
    rate_energy_H = df_temp.to_numpy()

    rate_dict = {'rate energy': df_overall['WoodMac'].to_numpy(),
                 'rate capacity': df_overall['ventyx'].to_numpy(),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict

def smud_rates(rate_years):
    import numpy as np
    winter = [54, 54, 54, 54, 54, 54,
              54, 54, 54, 54, 54, 54, 
              54, 54, 54, 54, 54, 75,
              75, 75, 54, 54, 54, 54]
    
    summer = [65, 65, 65, 65, 65, 65,
              65, 65, 65, 65, 65, 65,
              91, 91, 91, 91, 91, 150,
              150, 150, 91, 91, 91, 91]
    
    high_load = [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  50,
                   50,  50,  50,  5,  5,  5]
    
    jan = winter
    feb = winter
    mar = high_load
    apr = high_load
    may = high_load
    jun = summer
    jul = summer
    aug = summer
    sep = summer
    october = high_load
    nov = high_load
    dec = high_load
    
    month_rates = [jan,feb,mar,apr,may,jun,jul,aug,sep,october,nov,dec]
    month_days = [31,28,31,30,31,30,31,31,30,31,30,31]
    # populate rate energy for 1 year
    rate_energy_temp = []
    for i in range(len(month_days)):
        months_rate = month_rates[i]
        for days in range(month_days[i]):
            rate_energy_temp = rate_energy_temp + months_rate
    # Tile output for number of years the panels are active.
    rate_energy_H = np.tile(rate_energy_temp,rate_years)
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict
    
def uda_rates(rate_years):
    import numpy as np
    
    winter = [60,
              58,58,58,60,70,80,
              85,87,85,85,83,82,
              80,80,84,90,92,90,
              84,78,76,70,60]
    
    summer = [58,
              54,52,52,54,70,72,
              76,78,85,87,88,90,
              92,96,92,91,87,86,
              84,82,75,65,60]
    
    high_load = [  5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  5,  5,
                   5,  5,  5,  5,  50,  50,
                   50,  50,  50,  50,  5,  5]
    dec = winter
    jan = winter
    feb = winter
    mar = winter
    apr = high_load
    may = high_load
    jun = high_load
    jul = summer
    aug = summer
    sep = high_load
    october = high_load
    nov = high_load
  
              
              
    month_rates = [jan,feb,mar,apr,may,jun,jul,aug,sep,october,nov,dec]
    month_days = [31,28,31,30,31,30,31,31,30,31,30,31]
    # populate rate energy for 1 year
    rate_energy_temp = []
    for i in range(len(month_days)):
        months_rate = month_rates[i]
        for days in range(month_days[i]):
            rate_energy_temp = rate_energy_temp + months_rate
    # Tile output for number of years the panels are active.
    rate_energy_H = np.tile(rate_energy_temp,rate_years)
    rate_dict = {'rate energy': np.zeros(306600),
                 'rate capacity': np.zeros(306600),
                 'rate REC': np.zeros(306600),
                 'rate RA': np.zeros(306600),
                 'rate combined': rate_energy_H}
    return rate_dict