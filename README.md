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
Filename=Prototype_Amini.xlsx  ```input filename```
KNMI=True                         ```lookup KNMI data and add```
RenamedColumns=Tlv,Tsk,Tzo,Tamb,Eih,Eil,Eoh,Eol,Epv,Ecv1h,Ecv1c,T1cv1,T2cv1,Ecv2h,Ecv2c,T1cv2,T2cv2,E1wp,E2wp,Edhw,T1dhw,T2dhw,Vdhw,Sbd,Sra,Std,DateTime
          ```**transform** means of renaming columns. Can also take a list matching input length```
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
format = csv                   ```**linear**: chronologic data or ordered **csv**```
dataYear = 2020

[CategoryUnits]                   ```Each column in RenamedColumns need to be described according to below standard```
Tlv = °C,gebouwdata,"temperatuur woonkamer"
Tsk = °C,gebouwdata,"temperatuur slaapkamer"
Tzo = °C,gebouwdata,"temperatuur zolder"
Tamb = °C,gebouwdata,"temperatuur omgeving"
Eih = kWh,gebouwdata,"energie hoog tarief in"
Eil = kWh,gebouwdata,"energie laag tarief in"
Eoh = kWh,gebouwdata,"energie hoog tarief uit"
Eol = kWh,gebouwdata,"energie laag tarief uit"
Epv = kWh,gebouwdata,"energie zonnepanelen"
Ecv1h = kWh,gebouwdata,"energie warmtepomp zone 1 verwarmen"
Ecv1c = kWh,gebouwdata,"energie warmtepomp zone 1 koelen"
T1cv1 = °C,gebouwdata,"temperatuur in warmtepomp zone 1 verwarmen"
T2cv1 = °C,gebouwdata,"temperatuur uit warmtepomp zone 1 koelen"
Ecv2h = kWh,gebouwdata,"energie warmtepomp zone 2 verwarmen"
Ecv2c = kWh,gebouwdata,"energie warmtepomp zone 2 koelen"
T1cv2 = °C,gebouwdata,"temperatuur in warmtepomp zone 2 verwarmen"
T2cv2 = °C,gebouwdata,"temperatuur uit warmtepomp zone 2 koelen"
E1wp = kWh,gebouwdata,"energie zone 1 warmtepomp"
E2wp = kWh,gebouwdata,"energie zone 2 warmtepomp"
Edhw = kWh,gebouwdata,"energie warm tapwater"
T1dhw = °C,gebouwdata,"temperatuur in warm tapwater"
T2dhw = °C,gebouwdata,"temperatuur uit warm tapwater"
Vdhw = L,gebouwdata,"Liters warm tapwater"
Sbd = n,gebouwdata,"dimensieloos"
Sra = n,gebouwdata,"dimensieloos"
Std = n,gebouwdata,"dimensieloos"

[CategoryWeights]                   ```Each column in RenamedColumns need to be described according to below standard. This is required for statistical fault detection.```         
Tlv = 0,0.9,0.05,0,0.05,0
Tsk = 0,0.8,0,0,0.1,0.1
Tzo = 0,0.5,0,0,0.2,0.3
Tamb = 0,0,0,0,0,1
Eih = 0.3,0,0.1,0.5,0.1,0
Eil = 0.3,0,0.1,0.5,0.1,0
Eoh = 0.2,0,0,0.4,0.2,0.2
Eol = 0.2,0,0,0.4,0.2,0.2
Epv = 0,0,0,0.4,0,0.6
Ecv1h = 0,0.5,0.1,0.2,0.2,0
Ecv1c = 0,0.2,0.2,0.3,0.3,0
T1cv1 = 0,0,0.2,0,0.1,0.7
T2cv1 = 0,0.3,0.2,0.1,0.4,0
Ecv2h = 0.2,0.2,0.2,0.1,0.3,0
Ecv2c = 0,0.1,0.3,0.1,0.5,0
T1cv2 = 0,0,0.1,0,0.2,0.7
T2cv2 = 0,0.3,0.1,0.1,0.5,0
E1wp = 0.1,0.1,0.2,0.5,0.1,0
E2wp = 0.1,0.1,0.3,0.4,0.1,0
Edhw = 0.4,0.3,0,0.05,0.25,0
T1dhw = 0,0.1,0,0.025,0.075,0.8
T2dhw = 0,0.8,0,0.05,0.15,0
Vdhw = 0,1,0,0,0,0
Sbd = 0,0.7,0.2,0,0,0.1
Sra = 0,0.7,0.2,0,0,0.1
Std = 0,0.7,0.2,0,0,0.1

[eventdetection]
GenericEvents = 24,336,1.2,None    #Short window: 24h long windows:336 Delta stdev.p > 1,2 -> event
NormalizedEvents = 0.8             #Check what this does?
OtherEvents = Eventset_1,Eventset_2,Eventset_1 #refers to below 3 custom event detectors
Eventset_1 = 0.2,event_Vdhw_ra_336_24_1.2      #0.2: Vdhw running average is used to detect events
Eventset_2 = 0.2,event_HeatInput_ra_336_24_1.2
Eventset_3 = 0.2,event_COP_ra_336_24_1.2
Scanlist = Tavg,HeatInput               #Scan all those columns on errors```

[schil] #Hardly used
bouwjaar=1955
renovatiejaar=2019
meetjaar=2020
vloeroppervlak=120  #could be used in future for characteristic performance
schiloppervlak=60   #could be used in future for characteristic performance
glasoppervlak=8     #could be used in future for characteristic performance
pvoppervlak=5       #Is used to determine PV Performance [simplified
gas=0               #Is used to switch between heatpump and gas boiler calculations

[locatie]
orientatie=180
Location=Enschede
type_woning=tussenwoning
aantal_bewoners=1     #Is used to determine DHW curve
uren_buitenhuis=40

[model]
instance=Prototype_Amini   #Is used to store model parameters under, and retrieve them on a re-run. Also refers to all project related files.

[transform] #valuepairs of new_column = existing_column_name, serves for standardisation.
Tlv = Airsensorlivingroom_temperature_1_livingroom
Tsk = Airsensorlivingroom_temperature_2_livingroom
Tzo = Alklimaheatpump_room_temp
Tamb = Alklimaheatpump_outdoor_temp
Eih = Slimmemeter_kWhUsedHigh
Eil = Slimmemeter_kWhUsedLow
Eoh = Slimmemeter_kWhReturnedHigh
Eol = Slimmemeter_kWhReturnedLow
Epv = Growattinverter_total_energy_out
Ecv1h = Alklimaheatpump_total_energyHeating_produced
Ecv1c = Alklimaheatpump_total_energyHeating_produced
T1cv1 = Alklimaheatpump_total_energyHeating_produced
T2cv1 = Alklimaheatpump_total_energyHeating_produced
Ecv2h = Alklimaheatpump_total_energyHeating_produced
Ecv2c = Alklimaheatpump_total_energyHeating_produced
T1cv2 = Alklimaheatpump_total_energyHeating_produced
T2cv2 = Alklimaheatpump_total_energyHeating_produced
Edhw = Alklimaheatpump_total_energyDHW_produced
Vdhw = Waterflow_volume_out

[modules]  #Standardised calculation modules to execute on code execution.
SanityCheckE = 1                      # Sanity check Energy trends
EtoP = 1                              # Convert energy trends to Power trends
KNMI = 1                              # Utilize KNMI weather data
SanityCheckTamb = 1                   # Sanity check climate data
CalculateTavg = 1                     # Compile Tavg from multiple temperatures
DegreeDays = 1                        # Degree days calculation
EventDetection = 1                    # Event detection
GenericEvents = 1                     # Statistical generic event detection
ThermalBalance = 1                    # Create thermal balance based on preprocessing section
OpeningState = 0                      # Analyze boolean state values
SolarPanelAnalysis = 1                # Simplified solar panel performance estimate
EnergySignatureMethod = 1             # Apply heat signature method for RC estimation        
RCNetworkMethod = 1                   # Apply RC model method for RC estimation        
ElectricUserProfile = 1               # Calculate electric use profile based on balance
DHWUserProfile = 0                    # calculate DHW user profile based on measured data
BalanceDurationCurve = 1              # create duration curves for energy balance
TemperatureDurationCurve = 1          # create temperature duration curves
OtherEventDetectors = 1               # Extensive event detection
ColumnCategorization = 1              # Categorize columns
DataExport = 1                        # Export data
DHWDataDriven = 1                     # Use data driven DHW curve estimation
RCReversePowerCurve = 1               # Use the fitted RC model to approximate heating energy
SanityCheckThese = 1                  # Check the Scanlist data extensively on errors
dataCoverage = 0                      # Do a data coverage check, this DOES NOT execute the code. Gives insight in data coverage over the dataset!
COP = 0                               # Do Coefficient of Performance calculation
FastSim = 1                           # Run a simplified short simulation, to do tests or if you already have good coefficients
```

## Custom Analysis functions in analysis.py
Custom analysis or result visualisation can be done in analysis.py. This allows you to work with your own workflow, maybe you are used to different units, then you could do conversions here.
```
def skeleton(data,Log):
   data["new_column"] = (data["a"] * data["b"] / data["c"] - data["e"] + data["d"].sum())
   data["Tlv_k"] = data["Tlv"] + 273.15
   Log += "\n## Did something\n A*B/(C - E) + sum(D), cool\n\n"
   columns = ["new_column"]
   return data, Log, columns
```
