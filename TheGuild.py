import os
import requests
import json
import csv
import pandas as pd
import seaborn as sns
import numpy as np
import pprint as pp
pd.options.mode.chained_assignment = None 
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


"""Import Raw Data from Reservation DB/Inventory"""
# def pickle_DataFrame():
#     guild_excel = pd.read_excel('5. Reservation Raw Data.xlsx')
#     guildDF = pd.DataFrame(guild_excel)
#     guildDF.drop(['Unnamed: 27','Unnamed: 28','Unnamed: 29','Unnamed: 30'], axis=1, inplace=True)
#     guildDF = guildDF.to_pickle('guildDataFrame.pkl')
#       inventory_excel = pd.read_excel('6. Inventory Count Import.xlsx')
#       inventoryDF = pd.DataFrame(inventory_excel)
#       inventoryDF = inventoryDF.to_pickle('inventory.pkl')

# pickle_DataFrame()

def propertyInventory():
    inventoryDF = pd.read_pickle('inventory.pkl')
#TODO: """Didn't use Dicts can be deleted"""
    inventoryDict = inventoryDF.to_dict('list')
    inventoryDict.pop('index','columns')
    Jan_Property = dict(zip(inventoryDict['Property'],inventoryDict['Jan']))
    Feb_Property = dict(zip(inventoryDict['Property'],inventoryDict['Feb']))
    Mar_Property = dict(zip(inventoryDict['Property'],inventoryDict['Mar']))
    daysInMonth = {1:31,2:28,3:31,4:30,5:31,6:30,7:71,8:31,9:30,10:31,11:30,12:31}
    return(Jan_Property,Feb_Property,Mar_Property,daysInMonth)


"""Occupied Room Average = [Number of Rooms a Month] / [# of Days in Month]
   Occupancy Rate = [Occupied Room Average] / [Daily Inventory]
   RevPAR = Average Daily Rate * Occupancy Rate """

def occupancyRateMonthly():
    Jan_Property, Feb_Property, Mar_Property, daysInMonth = propertyInventory()
    inventoryDF = pd.read_pickle('inventory.pkl')

    
    
    guildDF = pd.read_pickle('guildDataFrame.pkl')
    adrPivot = pd.pivot_table(guildDF,index=['Month','Property','City'],values=['Average ADR','Number of Nights','Number of Rooms'],aggfunc={'Average ADR':np.mean,\
                                                                                                                    'Number of Nights':np.mean,\
                                                                                                                    'Number of Rooms':np.sum})


    adrPivot = adrPivot.reset_index()
    """Taking Sum of Total Monthly # of Rooms Occupied & dividing by Days in Month from Dictionary in Property Inventory Function"""
    adrPivot['Days'] = adrPivot['Month'].map(daysInMonth)
    adrPivot['Occupied Room Average'] = round(adrPivot['Number of Rooms']/adrPivot['Days'],6)
    adrPivot.drop(['Days'],axis=1,inplace=True)
    """Introducing Inventory Data into the DataFrame: See Variable Name Change"""
    adrPivotInv = adrPivot.set_index('Property').join(round(inventoryDF.set_index('Property'),0))
    
    """This can be cleaned up. Code is messy based on time to complete Case Study"""
    adrPivotInv = (adrPivotInv.reset_index())
    adrPivotInv = pd.pivot_table(adrPivotInv,index=['Month','Property','City'],values=['Month','Average ADR','Number of Nights',\
                                                                                'Number of Rooms','Occupied Room Average',\
                                                                                'Jan','Feb','Mar'])
 
    adrPivotJan = adrPivotInv.loc[1].drop(['Feb','Mar'],axis=1).reset_index()
    adrPivotFeb = adrPivotInv.loc[2].drop(['Jan','Mar'],axis=1).reset_index()
    adrPivotMar = adrPivotInv.loc[3].drop(['Jan','Feb'],axis=1).reset_index()
    
    """Combining All Months"""
    all_dfs = [adrPivotJan,adrPivotFeb,adrPivotMar]
    adrPivotInv = pd.concat(all_dfs,sort=True)
    adrPivotInv = adrPivotInv[['Property','Average ADR','Number of Nights','Number of Rooms','Occupied Room Average','Jan','Feb','Mar','City']]
  
    for k in adrPivotInv[['Jan','Feb','Mar']]:
        adrPivotInv[str(k)] = round(adrPivotInv['Occupied Room Average'] / adrPivotInv[str(k)],6)
    """Renamed Final Variable for Occupancy DF"""
    adrPivotOcc = adrPivotInv.rename(index=str, columns={"Jan": "Jan Occup Rate", "Feb": "Feb Occup Rate","Mar":"Mar Occup Rate"})
    return(adrPivotOcc)
occupancyRateMonthly()

"""Final Calculation for RevPAR"""
def revPar():
    Jan_Property, Feb_Property, Mar_Property, daysInMonth = propertyInventory()
    adrPivotOcc = occupancyRateMonthly().reset_index(drop=True)
    adrPivotOcc.at[5,'Jan Occup Rate'] = 0
    adrPivotOcc.at[17,'Feb Occup Rate'] = 0
    adrPivotOcc.at[29,'Mar Occup Rate'] = 0
    occupancyRate = adrPivotOcc[['Jan Occup Rate','Feb Occup Rate',\
                       'Mar Occup Rate']].stack(dropna=True)\
                        .reset_index(drop=True).to_frame('Occ')
    adrPivotOcc['Occupancy Rate'] = occupancyRate
    adrPivotOcc['Month'] = 0
    adrPivotOcc['Month'].loc[0:11] = 1
    adrPivotOcc['Month'].loc[12:23] = 2
    adrPivotOcc['Month'].loc[24:] = 3
    adrPivotOcc['Days'] = adrPivotOcc['Month'].map(daysInMonth)
    adrPivotOcc = adrPivotOcc.fillna(0)

    adrPivotOcc = adrPivotOcc[['Month','Days','Property','City','Average ADR','Number of Nights','Number of Rooms',\
                               'Occupied Room Average','Jan Occup Rate','Feb Occup Rate',\
                               'Mar Occup Rate','Occupancy Rate']]
    adrPivotOcc['RevPAR'] = round(adrPivotOcc['Average ADR'] * adrPivotOcc['Occupancy Rate'],6)
    adrPivotOcc = adrPivotOcc.reset_index(drop=True)
    adrPivotOcc.to_excel('Revpar.xlsx')
    return(adrPivotOcc)

def data():
    adrPivotData = revPar()
    adrPivotData.reset_index(drop=True)
    guildDF = pd.read_pickle('guildDataFrame.pkl')
    if guildDF['City'].isna().any() == True:
        print(guildDF['City'].isna())


data()