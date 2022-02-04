# -*- coding: utf-8 -*-
"""
Created on Tue Sep 28 08:40:57 2021

@author: Derek Ackerman
"""
def time_array(date_start,
               date_COD,
               months_pre_construction,
               months_construction,
               months_pre_COD,
               years_PPA,
               array_life):
    """
    Function to create an hourly date / time array, displaying booleans for different states 
    of construction, and project, written to match Matlab, currently only 
    in use for plotting x axis 

    Parameters
    ----------
    date_start : datetime object
        date the project starts.
    date_COD : datetime object
        date that the project is operational.
    months_pre_construction : int
        number of months from start to construction.
    months_construction : int
        number of months that the project is in construction.
    months_pre_COD : int
        number of months from completion to commercial operation. 
    years_PPA : int
        number of years the PPA is active
    array_life : int
        number of years that the modules are functional

    Returns
    -------
    date_time_out   :   array of date times for plotting

    """
    import datetime as dt
    import numpy as np

    # define day arrays for each month
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    #%% inputs for testing
    # array_life = 35
    # months_pre_construction = 25    # construction timing
    # months_construction = 6
    # months_pre_COD = 1
    # years_PPA = 12                  # PPA contract length
    # date_COD = dt.date(2022, 1, 1)    # Commercial operation date
    # date_start = (date_COD - \
        #               dt.timedelta(days=30*(months_pre_construction +
        #                           months_construction+months_pre_COD)))
        #%% body of function

    list_start = [int(i) for i in date_start.strftime('%Y%m%d')]
    list_COD = [int(j) for j in date_COD.strftime('%Y%m%d')]
    # weekday call returns 0-6, 0 = Monday, 6 = Sunday
    weekday_COD = date_COD.weekday()
    
    # temporary size, holding year, month, day, weekday, and PPA active boolean
    operational_array = np.empty([array_life*365*24, 5], dtype=int)
    cod_year_start = int(date_COD.strftime('%Y'))
    year_days = []
    operation_years = []
    year_months = []
    year_hours = []
    month_counter = 1
    for month in month_days:
        for day in range(1, month+1):
            for hour in range(0, 24):
                year_months.append(month_counter)
                year_days.append(day)
                year_hours.append(hour)
        month_counter += 1
    for year in range(0, array_life):
        cod_year = cod_year_start + year
        for hour in range(0, 8760):
            operation_years.append(cod_year)

    weekday_counter = []
    while len(weekday_counter) < len(operation_years):
        for hour in range(0, 24):
            weekday_counter.append(weekday_COD)
        if weekday_COD == 7:
            weekday_COD = 0
        else:
            weekday_COD += 1
    operational_array[:, 0] = operation_years
    operational_array[:, 1] = np.tile(year_months, array_life)
    operational_array[:, 2] = np.tile(year_days, array_life)
    operational_array[:, 3] = np.tile(year_hours, array_life)
    operational_array[:, 4] = weekday_counter

    date_time_out = []
    for row in range(0, len(operational_array)):
        date_time = dt.datetime(operational_array[row, 0],
                                      operational_array[row, 1],
                                      operational_array[row, 2],
                                      operational_array[row, 3])
        date_time_out.append(date_time)
        #date_time_out.append(matlab.date2num(date_time))    # convert to matlab datetime for plotting prior to plotly
        
    return(date_time_out)

            
