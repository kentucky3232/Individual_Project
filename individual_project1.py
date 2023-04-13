# -*- coding: utf-8 -*-


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import plotly.express as px
import os
import plotly.io as pio
pio.renderers.default='browser'

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

#graph plotting function
def graph_yr(graph):
    plot = graph.plot(lw = 0.3)
    plot.set(xlabel = "hours", ylabel = "kWh")
    
def graph_sum(graph):
    plot = graph.iloc[4128:4296].plot(lw = 1)
    plot.set(xlabel = "hours", ylabel = "kWh")
    
    
def graph_win(graph):
    plot = graph.iloc[0 : 168].plot(lw = 1)
    plot.set(xlabel = "hours", ylabel = "kWh")
    
def graph_check(graph):
    plot = graph.iloc[1344 : 1512].plot(lw = 1)
    plot.set(xlabel = "hours", ylabel = "kWh")


# validation inputs
# val = pd.read_csv("generic_profile_hourly.csv", sep = ",", header = 0)

# gas = val["gas hourly"] * 448
# elec = val["elec hourly"] * 448


#reading in csv input data
data = pd.read_csv("input.csv", sep = ",", header = 0)
weather = pd.read_csv("weather_data.csv", sep = ",", header = 0)
epc = pd.read_csv("epc_data.csv", sep = ",", header = 0)


#demand inputs
elec_demand = data["electrical demand"]#electrical demand from input spreadsheet
elec_demand = elec_demand.iloc[::2]
elec_demand = elec_demand.reset_index(drop = True)
hw_demand = data["hot water demand"]#hot water demand from input spreadsheet
hw_demand = hw_demand.iloc[::2]
hw_demand = hw_demand.reset_index(drop = True)
sh_demand = data["space heating demand"]#space heating demand from input spreadsheet
sh_demand = sh_demand.iloc[::2]
sh_demand = sh_demand.reset_index(drop = True)

#weather inputs
pv_elec = weather["solar electricity"]#electricity from solar PV (1kW capacity)
wind_elec = weather["wind electricity"]#electricity from wind (1kW capacity)
ambient_temp = weather["ambient_temp"]#ambient temperature for heat pump CoP equation

#epc data
floor_area = epc["Floor area (m2)"]
total_floor_area = floor_area.sum()



#convert demand to account for AECB Retrofit Standard (50kWh/m^2 per year)
aecb_standard = 50
aecb_allowance = aecb_standard * total_floor_area #total annual power aecb retrofit standard allows Barshare floor area
sh_scaling = sh_demand.sum() / aecb_allowance #required scaling of space heating in order to satisfy retrofit standards
sh_demand_retrofit = sh_demand / sh_scaling #new space heating demand after retrofit is applied


#convert hot water demand to account for boiler efficiency

#boiler efficiency
b_eff_winter = pd.DataFrame({"boiler efficiency" : [0.64]*((31+28+20)*24)})
b_eff_spring = pd.DataFrame({"boiler efficiency" : [0.69]*((11+30+31+21)*24)})
b_eff_summer = pd.DataFrame({"boiler efficiency" : [0.74]*((9+31+31+23)*24)})
b_eff_autumn = pd.DataFrame({"boiler efficiency" : [0.69]*((7+31+30+21)*24)})
b_eff_winter1 = pd.DataFrame({"boiler efficiency" : [0.64]*(10*24)})
b_eff = pd.concat([b_eff_winter, b_eff_spring, b_eff_summer, b_eff_autumn, b_eff_winter1], axis = 0, ignore_index = False)
b_eff = b_eff.reset_index(drop = True)


#hot water heat demand added to space heating post boiler efficiency evaluation
hw_demand_boiler = hw_demand / b_eff.loc[:,"boiler efficiency"]
net_heat_demand = hw_demand_boiler + sh_demand_retrofit




# Cop validation
jan = pd.DataFrame({"validation" : [3.08]*31*24})
feb = pd.DataFrame({"validation" : [3.09]*28*24})
mar = pd.DataFrame({"validation" : [3.22]*31*24})
apr = pd.DataFrame({"validation" : [3.28]*30*24})
may = pd.DataFrame({"validation" : [3.45]*31*24})
jun = pd.DataFrame({"validation" : [3.19]*30*24})
jul = pd.DataFrame({"validation" : [3.05]*31*24})     
aug = pd.DataFrame({"validation" : [3.20]*31*24})
sep = pd.DataFrame({"validation" : [3.20]*30*24})
octo = pd.DataFrame({"validation" : [3.40]*31*24})
nov = pd.DataFrame({"validation" : [3.23]*30*24})
dec = pd.DataFrame({"validation" : [3.13]*31*24})                  
copval = pd.concat([jan,feb,mar,apr,may,jun,jul,aug,sep,octo,nov,dec], axis = 0, ignore_index = False)
copval = copval.reset_index(drop = True)

#heat pump calculations (based off Staffell et al)
flow_temp = 45
temp_diff = flow_temp - ambient_temp
CoP_ASHP = 6.81 - 0.121 * temp_diff + 0.00063 * pow(temp_diff, 2)
CoP_GSHP = 8.77 - 0.15 * temp_diff + 0.000734 * pow(temp_diff, 2)
hp_demand_ASHP = net_heat_demand / CoP_ASHP
hp_demand_GSHP = net_heat_demand / CoP_GSHP

#Electrical demand post heat pump calculation: 
elec_demand_ASHP = hp_demand_ASHP + elec_demand
elec_demand_GSHP = hp_demand_GSHP + elec_demand

#Uncomment to see values:
# print(elec_demand_ASHP.sum()/(net_heat_demand.sum() + elec_demand.sum()))
# print(elec_demand_ASHP.sum())
# print(elec_demand)
# print(hw_demand)
# print(sh_demand)
# print(elec_demand.sum())
# print(hw_demand.sum())
# print(sh_demand.sum())
# print(elec_demand.sum() + hw_demand.sum() + sh_demand.sum())


# print(CoP_ASHP.iloc[(31+28+31+30+31+30+31+31+30+31+30)*24:(31+28+31+30+31+30+31+31+30+31+30+31)*24].mean(axis = 0)
# x = pd.DataFrame({"output":CoP_ASHP})
# plot = pd.concat([x, copval], axis = 1, ignore_index = False)
# plot.plot()

#use weather profile and renewable supply tools data to determine electrical output

pv_elec = pv_elec * 410 * 5 #pv capacity scaling
wind_elec = wind_elec * 2000 #wind capacity scaling
pv_elec_sum = pv_elec.sum()
wind_elec_sum = wind_elec.sum()
net_elec_gen = wind_elec + pv_elec #net renewable electricity generation
storage = 0 #storage capacity
storage1 = 0


# df = pd.DataFrame({"pv energy" : pv_elec,
#                    "wind energy" : wind_elec})

#Comparing supply to demand
sup_dem = net_elec_gen - elec_demand_ASHP
sup_dem1 = net_elec_gen - elec_demand_GSHP
step = pd.DataFrame({"supply against demand (ASHP)" : sup_dem,
                     "supply against demand (GSHP)" : sup_dem1})
step_storage = pd.DataFrame({"storage (ASHP)" : []})
step_storage1 = pd.DataFrame({"storage (GSHP)" : []})
step_provide = pd.DataFrame({"energy provided by storage (ASHP)" : []})
step_provide1 = pd.DataFrame({"energy provided by storage (GSHP)" : []})
st_pr = 0
st_pr1 = 0

# print(net_elec_gen)
# print(elec_demand_ASHP)
# print(sup_dem)


# sup_dem_neg = sup_dem[sup_dem < 0].sum()
# sup_dem_pos = sup_dem[sup_dem > 0].sum()
# print(sup_dem_neg)
# print(sup_dem_pos)

# plot1 = net_elec_gen.iloc[4128:4296].plot(lw = 1)
# plot1.set(xlabel = "hours", ylabel = "kWh")
# plot2 = elec_demand_ASHP.iloc[4128:4296].plot(lw = 1)
# plot2.set(xlabel = "hours", ylabel = "kWh")
# plot = sup_dem.iloc[4128:4296].plot(lw = 1)
# plot.set(xlabel = "hours", ylabel = "kWh")
# plot.legend(["Generation","Demand","Supply vs Demand"])


# df = pd.DataFrame({"supply vs demand" : sup_dem})
# df.iloc[4128:4296].plot(kind = "bar", color = (df["supply vs demand"] > 0).map({True:"g", False:"r"}))


# # storage calculations
st_check_df1 = pd.DataFrame({})
for index, row in step.iterrows():
    
    if row["supply against demand (ASHP)"] < 0:
        storage = storage + (row["supply against demand (ASHP)"] / 0.9)
        st_pr = -row["supply against demand (ASHP)"] / 0.9
    else:
        storage = storage + (row["supply against demand (ASHP)"])
        st_pr = 0
    if row["supply against demand (GSHP)"] < 0:
        storage1 = storage1 + (row["supply against demand (GSHP)"] / 0.9)
        st_pr1 = -row["supply against demand (GSHP)"] / 0.9
    else:
        storage1 = storage1 + (row["supply against demand (GSHP)"])
        st_pr1 = 0
    
    if storage > 0:
        storage = 0
    if storage1 > 5000:
        storage1 = 5000
    
    st = pd.DataFrame({"storage (ASHP)" : [storage]})
    st1 =  pd.DataFrame({"storage (GSHP)" : [storage1]})
    step_storage = pd.concat([step_storage, st], axis = 0, ignore_index = True)
    step_storage1 = pd.concat([step_storage1, st1], axis = 0, ignore_index = True)
    
    #energy provided by storage
    st_pr0 = pd.DataFrame({"energy provided by storage (ASHP)" : [st_pr]})
    st_pr10 = pd.DataFrame({"energy provided by storage (GSHP)" : [st_pr1]})
    step_provide = pd.concat([step_provide, st_pr0], axis = 0, ignore_index = True)
    step_provide1 = pd.concat([step_provide1, st_pr10], axis = 0, ignore_index = True)
    
sup_dem_st = sup_dem + step_provide["energy provided by storage (ASHP)"]
sup_dem_st1 = sup_dem + step_provide1["energy provided by storage (GSHP)"]

plot = pd.DataFrame({"supply and demand" : sup_dem,
                      "storage state" : step_storage["storage (ASHP)"]})

# graph_check(plot)
print(step_storage["storage (ASHP)"].min())

#minimum storage state check
# print(step_storage["storage (ASHP)"].min())

# # print(sup_dem[sup_dem>0].sum())

# PLOTLY GRAPH
sup_dem["colour"] = np.where(sup_dem.iloc[:8760]<0, 'red', 'green')
sup_dem_plot = px.scatter(sup_dem)
sup_dem_plot.update_traces(marker_color=sup_dem["colour"])
sup_dem_plot.show()

df = pd.DataFrame({"storage state" : step_storage["storage (ASHP)"],
                    "supply and demand" : sup_dem})


#outputs
# outputs = pd.concat([sh_demand_retrofit, hw_demand_boiler, net_heat_demand, hp_demand_ASHP, hp_demand_GSHP, elec_demand_ASHP, elec_demand_GSHP], axis = 1)
# outputs.columns = ["space heating demand post retrofit conversion", "hot water demand post boiler efficiency conversion", "net heat demand", "ASHP heat demand", "GSHP heat demand", "ASHP electric demand", "GSHP electric demand"]
# outputs.to_csv("outputs.csv")
# step_storage.to_csv("check.csv")
# b_eff.to_csv("check.csv")
