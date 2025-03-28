# TracknTrace
 Track building performance and Trace errors back to the source

```python.exe .\wrapper.py .\<file>.metadata -v```
```python categorizer/categorizer.py <file>```
From line #940 - #950 there is clean data which is suitable for analysis. Every code run also exports 8 files with clean data, suitable for further analysis:
 * ```<file>_afternoon.csv``` - afternoon from 12:00 to 17:00
 * ```<file>_daily.csv```     - daily data, for each 24h
 * ```<file>_evening.csv```   - evening data from 17:00 to 23:00
 * ```<file>_hour.csv```      - hourly data, each hour
 * ```<file>_monthly.csv```   - monthly data, for each 30 days
 * ```<file>_morning.csv```   - morning data, from 7:00 to 12:00
 * ```<file>_night.csv```     - nightly data, from 23:00 to 7:00
 * ```<file>_weekly.csv```    - weekly data, for every 7 days

## Install

pip install TracknTrace

## Performance Tracking
 * Multiple modules are defined to calculate performance of different aspects/components
    * A standardized way is provided utilized to build these Modules
    * Your own case specific modules can easily be implemented
    * The file analysis.py will be imported on runtime
      * All functions in analysis.py will be run against the input data
    * Input data availble under the name ```data```
    * Each custom function needs to return data, new columns, visualize boolean
      * data is updated on return, new columns are used to propagate information and for visualization.

## Error Tracing
There are many ways to lead back errors to the source data. One way that is provided:
 * For each dataset you indicate its correlation to 6 different error catagories
 * These corelations are automatically propagated into derived datasets
 * These correlations are combined with statistical outlier and fault detection

The aggregate of **all** correlations and outliers is a measure to link effect(s) to cause(s)

A typical metadata file looks like the delivered example, see below for possible options.


## Metadata
Every analysis starts with creating a file named ```<dataname>.metadata```. This file should at least contain the headers as discussed below. Or refer to the example ```Prototype_Amini.metadata``` which is supplied with the code.

```
[preprocessing]
Filename=Dongen121_2023_2024.csv  ```input filename```
KNMI=True                         ```lookup KNMI data and add```
RenamedColumns=transform          ```means of renaming columns. Can also take a list matching input length```
ThermalColumns=Ecv                ```Columns describing heating energy```
IndoorTemperatures = Tlv1,Tlv2,Tho```Air Temperatures measured in the building```
DoorWindowStates = None           ```States of doors and windows```
PVPanels = Ppv                    ```Solar Panel power column name```
HeatPumpElectric = Pwp            ```Heatpump input power column```
HeatPumpThermal = Pcv             ```Heatpump heating power column```
PositivePower = Pi,Ppv            ```All electric columns that are positive <gain>```
NegativePower = Po,Pwp            ```All electric columns that are negative <loss>```
DHWColumns = Pdhw                 ```Domestic Hot Water Power Column```
ResampleTime = 30T                ```Delta Time to resample all data towards```
format = linear                   ```**linear**: chronologic data or ordered **csv**```
dataYear = 2023

[CategoryUnits]                   ```Each column in RenamedColumns need to be described according to below standard```
Tlv1 = °C,gebouwdata,temperatuur woonkamer
Tlv2 = °C,gebouwdata,temperatuur woonkamer
CO2lv = ppm,gebouwdata,Co2 gehalte woonkamer
Tho = °C,gebouwdata,temperatuur zolder
Tamb = °C,gebouwdata,temperatuur omgeving
Ei = kWh,gebouwdata,energie hoog tarief in
Eo = kWh,gebouwdata,energie hoog tarief uit
Epv = kWh,gebouwdata,energie zonnepanelen
Ecv = kWh,gebouwdata,energie centrale verwarming
Edhw = kWh,gebouwdata,energie tapwater
Ewp = kWh,gebouwdata,energie warmtepomp
Vdhw = m3,gebouwdata,m3 warm tapwater cumulatief

[CategoryWeights]                   ```Each column in RenamedColumns need to be described according to below standard. This is required for statistical fault detection.```         
Tlv1 = 0,0.9,0.05,0,0.05,0
Tlv2 = 0,0.9,0.05,0,0.05,0
CO2lv = 0,0.9,0.05,0,0.05,0
Tho = 0,0.9,0.05,0,0.05,0
Tamb = 0,0,0,0,0,1
Ei = 0.3,0,0.1,0.5,0.1,0
Eo = 0.2,0,0,0.4,0.2,0.2
Epv = 0,0,0,0.4,0,0.6
Ecv = 0,0.5,0.1,0.2,0.2,0
Edhw = 0.4,0.3,0,0.05,0.25,0
Ewp = 0.1,0.1,0.2,0.5,0.1,0
Vdhw = 0,1,0,0,0,0

[eventdetection]
GenericEvents = 24,336,1.2,None    ```Short window: 24h long windows:336 Delta stdev.p > 1,2 -> event ```
NormalizedEvents = 0.8             ```Check what this does....?```
OtherEvents = Eventset_1,Eventset_2,Eventset_1 ```refers to below 3 custom event detectors```
Eventset_1 = 0.2,event_Vdhw_ra_336_24_1.2      ```0.2: Vdhw running average is used to detect events```
Eventset_2 = 0.2,event_HeatInput_ra_336_24_1.2
Eventset_3 = 0.2,event_COP_ra_336_24_1.2
Scanlist = Tavg,Pcv,Pwp,Pdhw,Ppv,HeatInput,Pi,Po,CO2lv ```Scan all those columns on errors```

[schil] ```Hardly used ```
bouwjaar=1955
renovatiejaar=2019
meetjaar=2020
vloeroppervlak=120  ```could be used in future for characteristic performance```
schiloppervlak=60   ```could be used in future for characteristic performance```
glasoppervlak=8     ```could be used in future for characteristic performance```
pvoppervlak=5       ```Is used to determine PV Performance [simplified]```
gas=0               ```Is used to switch between heatpump and gas boiler calculations```

[locatie]
orientatie=180
Location=Enschede
type_woning=tussenwoning
aantal_bewoners=1     ```Is used to determine DHW curve```
uren_buitenhuis=40

[model]
instance=Dongen_121   ```Is used to store model parameters under, and retrieve them on a re-run. Also refers to all project related files.```

[transform] ```valuepairs of new_column = existing_column_name, serves for standardisation.```
Tlv1 = Airsensorlivingroom_temperature_1_livingroom
Tlv2 = Airsensorlivingroom_temperature_2_livingroom
CO2lv = Airsensorlivingroom_co2_livingroom
Tho = Alklimaheatpump_room_temp
Tamb = Alklimaheatpump_outdoor_temp
Ei = Smartmeter_total_energy_in
Eo = Smartmeter_total_energy_out
Epv = Growattinverter_total_energy_out
Ecv = Alklimaheatpump_energyHeating_consumption
Edhw = Alklimaheatpump_energyDHW_consumption
Ewp = Heatpump_total_energy_in
Vdhw = Waterflow_volume_out

[modules]  ```Standardised calculation modules to execute on code execution.```
SanityCheckE = 1
EtoP = 1
KNMI = 1
SanityCheckTamb = 1
CalculateTavg = 1
DegreeDays = 1
EventDetection = 1
GenericEvents = 1
ThermalBalance = 1
OpeningState = 0
SolarPanelAnalysis = 1
EnergySignatureMethod = 1
RCNetworkMethod = 1
ElectricUserProfile = 1
DHWUserProfile = 0
BalanceDurationCurve = 1
TemperatureDurationCurve = 1
OtherEventDetectors = 1
ColumnCategorization = 1
DataExport = 1
DHWDataDriven = 1
RCReversePowerCurve = 1
SanityCheckThese = 1
dataCoverage = 0
COP = 0

```
