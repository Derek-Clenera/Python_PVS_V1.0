# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 15:07:37 2021

series of small helper functions that are not integral to the program, just 
clean up some of the processes


@author: Derek Ackerman
"""
def case_steps(start, 
               stop, 
               step):
    """
    function to take in a start, stop, and step and create an evenly spaced array 
    including the end case points

    inputs: 
        start: float
        stop:  float
        step:  float
    """
    temp = []                               # Create empty list
    if start == stop:                       # if start = stop, return only the start value
        temp.append(start)
    else:
        i = start                           # initialize at the starting value
        while i<stop:                       
            temp.append(i)                  # add the current value to the list
            i = i + step                    # update the case variable by the step value
        if round(i,2) == stop:              # round to 2 decimal places for error, compare to the stop value
            temp.append(stop)               # add the stop value to the list if necessary
    temp = [round(num,5) for num in temp]   # round the output to 5 decimal places to remove errors
    return temp

