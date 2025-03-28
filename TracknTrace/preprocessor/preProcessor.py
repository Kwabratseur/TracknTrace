#!/usr/bin/env python3
"""! @brief Defines the smart meter (pre)processor.

  @file preProcessor.py

  @brief Defines smart meter data preprocessor

  @section description_preProcessor Description
  Defines the base and end user class for all fitting purposes, model and data agnostic
  - multifitter

  @section libraries_preProcessor Libraries/Modules
  - random standard library (https://docs.python.org/3/library/random.html)
    - Access to randint function.
  - argparse input argument parsing, adding options to command-line usage
  - pandas dataframe library
  - sys for handling files and folders and detecting OS
  - configparser for handling configuration/metadata files
  - warnings to create own warnings and ommit others
  - matplotlib plotting Library
  - sklearn for linear regressions on usage patterns/energy signatures
  - mufit multi fitter for model fitting library
  - inspect to convert code to pretty output and to generate equations
  - pytexit to generate latex equations
  - io for file/image handling. Internal image passing format.
  - os for OS detection and folder handling
  - PIL for internal image passing
  - copy for making pandas deepcopies
  - markdown for generating pretty output
  - datetime standard library

  @section notes_preProcessor Notes
  - This code expects a .CSV file with smart meter data with additional columns containing indoor and outdoor temperatures.
  - A .metadata file is filled according to a standard format
  - data will be read and manipulated according to instructions in the .metadata file

  @section todo_preProcessor TODO
  - Create Documentation
  - create visualization of inner workings
  - convert to powerpoint?
  - use data from chris to tune these models
  - annemarie: boxplot tool
  - EB monitorting: what to do with data

  @section author_sensors Author(s)
  - Created by Jeroen van 't Ende 26/09/2024

  Copyright (c) 2024 Jeroen van 't Ende.  All rights reserved.

"""
import random
import math
import argparse
import pandas as pd
import datetime as datime
import seaborn as sns
import sys
import configparser
import warnings
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from mufit.main import *
import inspect
from pytexit import py2tex
import io
import os
from PIL import Image, ImageChops
import copy
import markdown
import pytz
from TracknTrace import analysis
from inspect import getmembers, isfunction
import matplotlib as mpl
mpl.rcParams.update(mpl.rcParamsDefault)
plt.rcParams['text.usetex'] = False
## Ignore FutureWarning errors, floods log
warnings.simplefilter(action='ignore', category=FutureWarning)



## Variable containing type of OS the code is running on
OS = os.environ.get('OS','')
print("Hello, I'm running on {}".format(OS))

## plotting backend for pandas
pd.options.plotting.backend = "plotly"
## turn of error reporting for chained assignments
pd.options.mode.chained_assignment = None

## Argument parser, filled with Commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str,
                    help="Input filename")
parser.add_argument("-v", "--verbose", action="count",
                    help="increase output verbosity", default=0)

## Instantiate the parser
args = parser.parse_args()

if args.verbose:
    print(args)
    print(sys.path)
else:
    print("No verbosity!")


class Eventor(object):
    """Provides Generic math and statistic based event detection methods."""
    def __init__(self, data, metadata=None, VERBOSE=0):
        """! The Eventor base class initializer.

        @param data  Data to fingerprint on events
        @param metadata   Metadata describing the data, is not required
        @param VERBOSE  verbose integer generates more output for debugging

        @return  An instance of the eventor class initialized.
        """
        ## internal verbosity switch, for testing.
        self.VERBOSE = VERBOSE
        ## input data loaded at initialization
        self.data = data.copy()
        ## stores statistical description of input data
        self.statistics = data.describe()
        ## timestep in dataset, column must be named dt
        self.dt = self.statistics["dt"]["mean"]  # use to determine shortwindow and longwindow for generic detections?
        ## list of columns in data
        self.columns = list(data.columns)
        if metadata is not None:
            ## metadata of data.
            self.metadata = metadata
        if self.VERBOSE:
            print("Data loaded, metadata and statistics instantiated. Ready for event indexing...")
            self.slidingWindow("Tavg")
            self.runningAverages("Tavg").plot()

    def Resample(self, NewDelta="30m"):
        """! Resample the loaded data

        @param NewDelta  string which indicates to what interval to resample the data towards.
        """
        self.data = self.data.resample(NewDelta).mean().interpolate()
        self.statistics = data.describe()

    def slidingWindow(self, trend, size = 6, sd = 2):
        """! Load a dictionary of variables and add in dt

        @param trend  Which column from the data to check for events
        @param size  Size of the window over which to calculate the standard deviation
        @param sd  standard deviation exceedance which is considered an event

        @return  A new dataframe with ones where events are detected
        """
        return self.data[trend].rolling(window=size).mean().apply(lambda x: 1 if x > self.statistics[trend]["mean"] + sd*self.statistics[trend]["std"] else (-1 if x < self.statistics[trend]["mean"] - sd*self.statistics[trend]["std"] else 0))# ADD RESampling

    def runningAverages(self, trend, longWindow=42, shortWindow=6, sd=2): # Also edge detection when windows are set properly (e.g. 4, 1 or 2, 1)
        """! Load a dictionary of variables and add in dt

        @param trend  Which column from the data to check for events
        @param longWindow  Length of the long window which is the base for comparison
        @param shortWindow  Length of the short window, if this sd is x times higher
        @param sd  standard deviation exceedance which is considered an event

        @return  A new dataframe with ones where events are detected
        """
        sw = self.data[trend].rolling(window=shortWindow).mean().bfill().copy()
        for i, x in enumerate(self.data[trend].rolling(window=longWindow).mean().bfill()):
            if sw[i] > x + sd*self.statistics[trend]["std"]: # Rising
                sw[i] = 1
            elif sw[i] < x - sd*self.statistics[trend]["std"]: # Falling
                sw[i] = -1
            else:
                sw[i] = 0
        return sw

    def GenericEvents(self, shortWindow = 8, longWindow = 48, sd = 2, columns = None):
        """! Detect events for all columns in self.data, runs runningAverages and slidingWindow

        @param longWindow  Length of the long window which is the base for comparison
        @param shortWindow  Length of the short window, if this sd is x times higher it is detected as an event
        @param sd  standard deviation exceedance which is considered an event
        @param columns  Which dwstateColumns from the data to check for events

        @return  A new dataframe with ones where events are detected
        """
        if columns is None:
            columns = self.columns
        for i in columns:
            if "event" not in i:
                self.data["event_{}_sw_{}_{}".format(i, shortWindow, sd)] = self.slidingWindow(i, shortWindow, sd)
                self.data["event_{}_ra_{}_{}_{}".format(i, longWindow, shortWindow, sd)] = self.runningAverages(i, longWindow, shortWindow, sd)
        self.columns = list(self.data.columns)
        ## list of columns describing detected events
        self.eventcolumns = [x for x in self.columns if "event" in x]
        self.data["normevents"] = self.data[self.eventcolumns].abs().sum(axis=1)/float((self.data[self.eventcolumns].abs().sum(axis=1)).max())
        self.eventcolumns.append("normevents")
        self.columns = list(self.data.columns)
        self.statistics = self.data.describe()

    def EventIndicer(self, threshold = 0.5, trend="normevents"):
        """! Detect events for all columns in self.data, runs runningAverages and slidingWindow

        @param threshold  threshold value of the sum of detections on any moment, if bigger then this value it is counted as an event
        @param trend  the suffix or prefix that is filtered out and summed for each index

        @return  A new event based on existing events
        """
        events = []
        c = 0
        Detection = False
        for i, x in enumerate(self.data[trend]):
            if x > threshold:
                Start = i
                Detection = True
            elif x < threshold and Detection:
                events.append({"Event":"{}_{}".format(c,trend), "start_index":Start, "start_date":self.data.index[Start].strftime("%d-%m-%Y %H:%M:%S"), "end_index":i, "end_date":self.data.index[i].strftime("%d-%m-%Y %H:%M:%S")})
                Detection = False
                c += 1
        return events  # test.data.iloc[event[i]["start_index"]:event[i]["end_index"]]

    def EventCategorizer(self, categories): # create a sum of category data, each event at each t added up to the 6 category columns
        """! Summarizes all detected events to a limited group of categories

        @param categories  a list of name:category to translate any column to a new category

        @return  A new dataframe with events linked to categories
        """
        ## Categorial filter applied to detected events
        self.CatData = pd.DataFrame(columns = categories[0], index = self.data.index)
        self.CatData = self.CatData.fillna(0.0)
        dfv = pd.DataFrame(categories[1:],columns=categories[0], index=[i[0] for i in categories[1:]]).drop("Combined_Categories",axis=1)
        for i in self.eventcolumns:
            if i != "normevents":
                if i.split("_")[1] in dfv.index:
                    for j in self.data[[i]].T:
                        if self.VERBOSE > 5:
                            print("{} found in data, doing something with:".format(i))
                            print(i,j, self.data[[i]].T[j], float(self.data[[i]].T[j])*dfv.loc[i.split("_")[1]])
                            #print(self.data[[i]].mul(dfv.T[i.split("_")[1]].T))
                        self.CatData.T[j] += abs(self.data[[i]].T[j])*dfv.loc[i.split("_")[1]]
        return self.CatData

def EventCategorizerFcn(categories, data):
    """! Summarizes all detected events to a limited group of categories, does the same as internal class function EventCategorizer but requires data.

    @param categories  a list of name:category to translate any column to a new category
    @param data  a list of input data to categorize.

    @return  A new dataframe with events linked to categories
    """
    df = pd.DataFrame(columns = categories[0][1:], index = data.index)
    df =  df.fillna(0.0)
    print(df)
    for i in data[["Tlv"]].T:
        print(i, data[["Tlv"]].T[i], float(data[["Tlv"]].T[i])*cats.loc["Tlv"])
        df.T[i] += float(data[["Tlv"]].T[i])*cats.loc["Tlv"]# ## $ FINALLY TYHIS DOESD OETGIOGFEIHAOFAWIO{WFG
    return df

def VisualizeEvent(df, event, Instance, Extra = None, columns = None, Size = None, Type="default", Save = True):
    """! Summarizes all detected events to a limited group of categories

    @param event finish this!!

    @return  A new dataframe with events linked to categories
    """
    if Size is None:
        plt.rcParams['figure.figsize'] = 8., 4.
    else:
        plt.rcParams['figure.figsize'] = Size[0], Size[1]
    if columns is None:
        columns = ["Tavg", "Tamb", "dT", "Pdhw","Pin","UAct"]
    if Extra is None:
        Extra = int(len(df.iloc[event["start_index"]-1:event["end_index"]+1])*1.5)
    prows = 2
    pcols = 3
    while len(columns) > prows*pcols:
        prows += 1
    fig, axs = plt.subplots(nrows=prows, ncols=pcols, layout='constrained')
    fig.suptitle("Event {}  From: {} To: {} - What is going on here?".format(event["Event"], event["start_date"], event["end_date"]), fontsize=14)
    c = 0
    def plotEvent(ax):

        ax.plot(df.iloc[event["start_index"]-Extra:event["start_index"]][columns[c]], color="b") # plot 1.5x event steps before event in blue
        ax.plot(df.iloc[event["start_index"]-1:event["end_index"]+1][columns[c]], color="r") # plot event in RED
        ax.plot(df.iloc[event["end_index"]:event["end_index"]+Extra][columns[c]], color="b") # plot 1.5x event steps after event in blue
        #ax.set_xlabel('time', fontsize=10)
        ax.set_title(columns[c], fontsize=12)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=25, fontsize=6)

    for ax in axs.flat:
        if c >= len(columns):
            break
        plotEvent(ax)
        c += 1
    if Save:
        fig.savefig("event_{}_{}.png".format(event["Event"], Instance))
    fig.tight_layout()


def Stochastic_Usage(H,Size=1.0):
    """Empirical equation for Domestic Hot Water usage.

    @param H  Hour of the day for which to get the L/h value
    @param Size  size of household, number of inhabitants

    @return  A new dataframe with events linked to categories
    """
    UsageConst = 120 + random.randint(-20,20) # +/- some randomness, usageconstant is +/- total L a user requires
    Set = [[0.45*Size*UsageConst,7.7,1.2],[0.15*Size*UsageConst,12.5,2],[0.4*Size*UsageConst,19.5,2.7]]
    result = 0
    def StochFcn(T,f,mu,sigma): # Actual function for stochastic DHW usage determination
        return (f/(sigma*math.sqrt(2*math.pi)))*math.exp(-0.5*((T-mu)/sigma)**2)
    for i in Set:
        result += StochFcn(H,i[0],i[1],i[2])
    return result/1000# L/s


def linint(x1,x2,y1,y2):
    """Linear interpolation.

    @param x1  value  (x2-x1)
    @param x2  value  (x2-x1)
    @param y1  value  delta = y2-y1
    @param y2  value  delta = y2-y1

    @return x2-x1 frames interpolated between y2 and y1"""
    Delta = y2-y1
    Frames = []
    for i in range(x2-x1):
        Frames.append(y1+Delta*(i+1))
    return Frames

def SimilarityCheck(df,data, corrector, ULimit = 50.0, LLimit = -15.0, ROCLimit = 30.0/(12.0*60*60), VERBOSE=0):
    """General sanity and similarity check

    @param df  base dataframe containing all series to work with
    @param data  name of column in dataframe which needs to be corrected
    @param corrector  name of column in dataframe which can be used to correct data
    @param ULimit  the upper limit, exceeding this value means that values from corrector will be taken
    @param LLimit  the lower limit, going below this value means that values from corrector will be taken
    @param ROCLimit  if this Rate Of Change is exceeded, values from corrector are taken
    @param VERBOSE  if this value is bigger the 0, corrected values will be reported in the log with more details

    @return The original dataframe but with the data column fixed according to above  rules."""
    prev = 0
    for i, x in  enumerate(df[data]):
        if x > ULimit or x < LLimit:
            df[data][i] = df[corrector][i]
            if VERBOSE > 0:
                print("Detected error at {} , x = {} < {} and > {}. Replaced for {}".format(i, x, ULimit, LLimit, df[corrector][i]))
        if i != 0 and i != len(df):
            if abs(x - prev)/df["dt"][i] > ROCLimit:
                if VERBOSE > 0:
                    print("ROC Exceedance {} , x = {} > {}. Replaced for {}".format(i, abs(x - prev)/df["dt"][i], ROCLimit, df[corrector][i]))
        prev = x
    # data is the trend we want to repair/check. This is basicaully used for calculations down the line and we NEED good data here.
    # corrector is the corrector trend, which contains only good data. This must be assigned manually for each case.
    return df

def EnvironmentTemperatureCheck(df, ROCLimit = 30.0/(12.0*60*60), ULimit = 50.0, LLimit = -15.0, VERBOSE=0):
    # Assumption is that temperature never goes above 50 degrees celsius
    # and that it does not change faster then a certain rate of change per time unit

    for i in df:
        prev = 0
        indexerr = 0
        err = False
        next = 0
        indexend = 0
        for j, x in enumerate(df[i]):
            if j == 0:
                err = False
                prev = x
            if (abs(x- prev)/df["dt"][j] > ROCLimit or x > ULimit) and not err:
                err = True
                indexerr = j
                if VERBOSE > 0:
                    print("Found error in {}, {} < {} at i = {}".format(i, x, prev, j))
                prev = x
            elif not err:
                prev = x
            if err:
                if abs(x- prev)/df["dt"][j] < ROCLimit and x < ULimit:
                    if VERBOSE > 0:
                        print("Error for {} seems to be restored at {}, {} > {}; error continues for {} dataframes".format(i, j, x, prev, j-indexerr))
                    indexend = j
                    next = x
                    err = False
                    GeneratedFrames = linint(indexerr,indexend,prev,next)
                    for k,z in enumerate(GeneratedFrames):
                        old = df[i][indexerr+k]
                        df[i][indexerr+k] = z
                        if VERBOSE > 2:
                            print("Set {} from {} to {}, now: {}".format(indexerr+k, old, z, df[i][indexerr+k]))
                    if VERBOSE > 1:
                        print("{} frames were generated to fill the gap from {} to {}".format(GeneratedFrames, indexerr, indexend))
    return df

def RepairCumulatives(df,VERBOSE=0):
    """Repair cumulative trends from smart meter data.

    @param df  input cumulative trends dataframe to repair
    @param VERBOSE  verbosity switch to generate reports for different levels of knowledge

    @return dataframe with actually cumulative trends."""
    for i in df:
        prev = 0
        indexerr = 0
        err = False
        next = 0
        indexend = 0
        for j, x in enumerate(df[i]):
            if j == 0:
                prev = x
                err = True
            if x < prev and not err:
                err = True
                indexerr = j
                if VERBOSE > 0:
                    print("Found error in {}, {} < {} at i = {}".format(i, x, prev, j))
                prev = x
            elif not err:
                prev = x
            if err:
                if x > prev:
                    if VERBOSE > 0:
                        print("Error for {} seems to be restored at {}, {} > {}; error continues for {} dataframes".format(i, j, x, prev, j-indexerr))
                    indexend = j
                    next = x
                    err = False
                    GeneratedFrames = linint(indexerr,indexend,prev,next)
                    for k,z in enumerate(GeneratedFrames):
                        old = df[i][indexerr+k]
                        df[i][indexerr+k] = z
                        if VERBOSE > 2:
                            print("Set {} from {} to {}, now: {}".format(indexerr+k, old, z, df[i][indexerr+k]))
                    if VERBOSE > 1:
                        print("{} frames were generated to fill the gap from {} to {}".format(GeneratedFrames, indexerr, indexend))
    return df


def PdTtoV(x, T1, T2, Pdhw):
    """Calculate DHW flow rate based on temperature difference and power.

    @param x  series with power of domestic hot water
    @param T1  value  (x2-x1)
    @param T2  value  delta = y2-y1
    @param y2  value  delta = y2-y1

    @return x2-x1 frames interpolated between y2 and y1"""
    rho = 1008.0
    cp = 4.2
    return (x[Pdhw] / rho*cp*(x[T1]-x[T2]))  # returns m3/s


def fracH(dt):
    """Calculate the fraction of an hour, for interpolation.

    @param dt datetime time object

    @return decimal number between 0 and 24"""
    frach = 0.0
    if dt.minute != 0 or dt.second != 0:
        frach = ((dt.minute*60 + dt.second)/3600.0)
    return float(dt.hour) + frach


def PandasDHWWrapper(x, Inhabitants = 1):
    """Wrap for Domestic Hot Water empirical equation for Pandas Apply.

    @param x  a pandas dataframe to which DHW will be appended
    @param Inhabitants  amount of inhabitants for which to generate a DHW profile

    @return DHW profile for """
    frach = fracH(x.name)
    return Stochastic_Usage(frach, Inhabitants)


def LogReport(msg, verbosityLimit = None):
    """Function to unify logging, messaging, errors and report generation.

    @param msg  Message to append to log or report
    @param verbosityLimit The verbosity number connected to this message.

    @return sets Log, Verbosity and Headers for every message"""
    global Log
    global Verbosity
    global Headers
    if verbosityLimit is None:
        verbosityLimit = Verbosity
    else:
        Verbosity = verbosityLimit
    if args.verbose >= verbosityLimit:
        print(msg)
        Log += "\n\n" + str(msg) + "\n"
        if str(msg)[0] == "#":
            Headers += str(msg)
            Headers += "\n"


def logFigure(title, data, Instance, fig = None, sort = None, kind = None, verbosityLimit = None):
    """Add figure to the created log. And make sure it is rendered properly in HTML

    @param title  the name of the figure under which it will be saved
    @param data  the data to plot in the figure
    @param fig  the figure object to plot, to allow customization but still end up in log/report.
    @param sort  If the data to be plotted needs to be sorted or not, generates time-duration curves.
    @param kind  type of matplotlib plot to generate (line, bar, etc.)

    @param return  Adds figure to Log, either HTML or a link to the output figure."""
    global Log
    global Verbosity
    if verbosityLimit is None:
        verbosityLimit = Verbosity
    else:
        Verbosity = verbosityLimit
    if kind == None:
        kind = "line"
    if fig == None:
        pd.options.plotting.backend = "plotly"
        if sort == None:
            fig = data.loc[:, data.columns != 'DateTime'].plot(kind=kind)
        else:
            fig = data.loc[:, data.columns != 'DateTime'].resample("1h").mean().interpolate().sort_values(sort,ascending=False).reset_index(drop=True).plot(kind=kind)
    figname = '{}_{}.html'.format(title, Instance)
    Str = fig.write_html(figname, auto_open=False)
    with open(figname, 'r', errors="ignore") as f:
        plotly_html = f.read()
    LogReport("__"*80)
    LogReport("# {}".format(title))
    if args.verbose >= Verbosity:
        Log += "\n" + plotly_html


def Carnot(Tc,Th):
    """Calculate Carnot efficiency.

    @param Tc  cold temperature in celsius.
    @param Th  hot temperature in celsius.

    @return Carnot efficiency"""
    c = 273.15
    return 1/(1-((c+Tc)/(c+Th)))


def COP(Pth,Pel):
    """Calculate Coefficient of Performance.

    @param Pth  Thermal power units do not matter as long as they are both the same.
    @param Pel  Electrical power, units do not matter as long as they are the same.

    @return Coefficient of Performance"""
    try:
        COP = Pth/Pel
    except:
        COP = 0.0
    return COP


def TimeDivision(df,Columns,scaleArray = None, reverse = False):
    """Find delta in dataset and divide Columns by time.

    @param df  input dataset containing columns to divide by time
    @param Columns  Columns to divide by time. Delta will be detected automatically
    @param scaleArray  Scaling to apply when dividing by time
    @param reverse  Reverse the operation or not.

    @return df  return the transformed dataframe. Calling same function with identical arguments but reverse = True returns to the original."""
    dt = (df.index[1] - df.index[0]).total_seconds() # find delta time
    if scaleArray is None: # if scale array was not define, fill it with ones
        scaleArray = []
        for i in Columns:
            scaleArray.append(1.0)
    for i, x in enumerate(Columns): # for each item, do a persistent scaling edit
        if not reverse:
            df[x] = df[x]*scaleArray[i]/dt
        else:
            df[x] = df[x]*dt
    return df


def KNMI_Resampler(FileName, T_Columns, ScaleArray, RevertArray = None, Interval = "5min",header = 28, Export=False,plot=False): #  header is the line with the hashtag#!
    """! KNMI file reader with different output modi.

    @param  FileName  the filename with KNMI data to open, can include the path
    @param T_Columns  Time independent columns; the code needs to be aware of these in order to correctly interpolate. Array of strings.1
    @param ScaleArray  Scales T_Columns, amount of items should match T_Columns
    @param RevertArray  Revert T_Columns through the scalars given here, amount of items should match T_Columns
    @param Interval  Time interval to interpolate or extrapolate towards. Can be a string like 5s, 5min, 1h, 1d, etc.
    @param header  Number of lines to skip for the header line. Open the input file to find this.
    @param Export  If the resulting data needs to be exported to .CSV for future use or not. True or False
    @param plot  If set to True, a plot will be opened on completion.

    @return A Pandas dataFrame transformed as configured
    """
    KNMI = pd.read_csv(FileName,header =header ,sep=",",na_values="     ")     # open the file
    print(KNMI)
    FixHour = lambda x: "0{}".format(x-1) if len(str(x-1)) == 1 else str(x-1)  # fix hours in file
    KNMI["   HH"] = KNMI["   HH"].apply(lambda x: FixHour(x))                          # apply the fix
    KNMI["Time"] = KNMI.YYYYMMDD.map(str) +" "+ KNMI["   HH"].map(str)                # combine date and time
    KNMI["Time"] = pd.to_datetime(KNMI.Time, format="%Y%m%d %H")               # convert datetime to datetime.datetime indexed object
    KNMI = KNMI.drop(["   HH","# STN","YYYYMMDD"],axis=1)                          # drop useless columns
    KNMI = KNMI.set_index("Time")                                              # set index as time column
    KNMI = KNMI.shift(periods=1).bfill()
    KNMI = TimeDivision(KNMI,T_Columns, ScaleArray)                            # convert time independent columns to time dependent columns
    KNMI = KNMI.resample(Interval).mean().interpolate()                               # now do the interpolation!
    if RevertArray is not None:                                                # if a revert array was defined
        KNMI = TimeDivision(KNMI,RevertArray, ScaleArray, reverse = True)      # revert the columns to their original units with new delta t
    NewFileName = "{}_{}.csv".format(FileName.split(".")[0],Interval)
    if Export:
        KNMI.to_csv(NewFileName)
    if plot:
        KNMI.plot()
    KNMI["    T"] = KNMI["    T"]*0.1 # scale to C
    KNMI["    FF"] = KNMI["   FF"]*0.1 # scale to mm
    return KNMI[["    T","    Q","   DD","   FH","   RH"]] # returns temperature, solar radiation, wind direction, wind speed, rainfall. Anything that can influence thermal balance.


## Defining the color white for latex
white = (255, 255, 255, 255)

def latex_to_img(tex):
    """Convert Latex expression to .png image

    @param tex  the latex expression to convert to an image

    @return an html compatible image? (check this!)"""
    buf = io.BytesIO()
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.axis('off')
    plt.text(0.05, 0.5, f'${tex}$', size=40)
    plt.savefig(buf, format='png')
    plt.close()

    im = Image.open(buf)
    bg = Image.new(im.mode, im.size, white)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    return im.crop(bbox)

def Lambda2Tex(lmd, VERBOSE=0):
    """Convert Lambda system of equations to latex

    @param lmd  lambda function to convert
    @param VERBOSE  retardcounter higher = less retarded

    @return the converted equation in tex format"""
    f = inspect.getsourcelines(lmd)[0][0].split(":")
    eq = f[0].split('"')[1]
    if VERBOSE > 0:
        print(eq)
    fcn = f[-1].split(",")[0].split("}")[0]
    if VERBOSE > 1:
        print(fcn)
    eq = eq + " =" + fcn
    if VERBOSE > 2:
        print(eq)
    return eq


CategoryWeights = [["Combined_Categories", "User_Electric", "User_Thermal", "Building_thermal", "Installation_Electric", "Installation_Thermal", "Weather_thermal"]]#,
BaseWeights = [["Combined_Categories", "User_Electric", "User_Thermal", "Building_thermal", "Installation_Electric", "Installation_Thermal", "Weather_thermal"],
                ["Tlive", 0, 0.9, 0.05, 0, 0.05, 0],
                ["Ttraffic", 0, 0.5, 0, 0, 0.2, 0.3],
                ["Tambient", 0, 0.5, 0, 0, 0.2, 0.3],
                ["Emachine", 0.1, 0.1, 0.2, 0.5, 0.1, 0]]


def DerivedCategory(trends, newtrend, CategoryWeights, Verbose=0):
    """Derive categories from initial guesses.

    @param trends  The base trend from which to derive
    @param newtrend  The derived trends which categories still need to be determined
    @param CategoryWeights  The original category weights used for base trends, which will derive to new trends
    @param Verbose  Verbosity switch for debugging

    @return the same dataframe as trends but with newtrends added and with derived categories"""
    try:
        if Verbose > 2:
            print(CategoryWeights)
            print("Merging:")
            for z in trends:
                print(z, [i for i in CategoryWeights if z in i[0]][0])
            print("__"*32)
        if len(trends) < 1:
            cat = copy.deepcopy([i for i in CategoryWeights if trends[0] in i[0]][0])
            cat[0] = newtrend
            return cat
        else:
            #print(CategoryWeights, trends)
            cat = [i for i in CategoryWeights if trends[0] in i[0]][0]
            if Verbose > 2:
                print(trends[0], cat)
            for z in trends[1:]:
                Addcat = [i for i in CategoryWeights if z in i[0]][0]
                if Verbose > 2:
                    print(z, cat)
                cat = [(Addcat[i] + x)/2 if i != 0 else x for i, x in enumerate(cat)]
            cat[0] = newtrend
            if Verbose > 2:
                print("__"*32)
                print(cat, sum(cat[1:]))
            return cat
    except:
        print("Derriving categories failed for {}".format(newtrend))
        return trends

def AnalysisDealer(data, analysis):
    """Apply all user defined functions from analysis.py to data

    @param data  Standardized input (pandas)dataframe.
    @param analysis  a list of [[name:function],] of user defined functions

    @return data the transformed dataframe"""
    global Log
    LogReport("__"*80, 2)

    for fcn in analysis:
        LogReport("# {}".format(str(fcn[0])))
        data, Log, columns = fcn[1](data, Log)
    return data


## Variable contains the generated Log, equal to code output in commandline.
Log = ""
## Headers of document. Created Table of Content.
Headers = "# Table Of Content\n " + "__"*100
## For which level of knowledge to generate a report.ssss
Verbosity = 1

dhw1 = []
dhw2 = []
dhw3 = []
dhw4 = []
dhw5 = []
dhw6 = []
dhw7 = []
dhw8 = []
index = []
for i in range(24):
    print()
    dhw1.append(Stochastic_Usage(i,1))
    dhw2.append(Stochastic_Usage(i,2))
    dhw3.append(Stochastic_Usage(i,3))
    dhw4.append(Stochastic_Usage(i,4))
    dhw4.append(Stochastic_Usage(i,5))
    dhw4.append(Stochastic_Usage(i,6))
    dhw4.append(Stochastic_Usage(i,7))
    dhw4.append(Stochastic_Usage(i,8))
    index.append(i)
## Domestic hot water lookup table
dhw = [[index,dhw1], [index,dhw2], [index,dhw3], [index, dhw4], [index, dhw5], [index, dhw6], [index, dhw7], [index, dhw8]]


def ProcessData():
    """! Example main to run if file is not being imported
    """
    global Log
    global Headers
    global CategoryWeights
    CategoryUnits = []

    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    result_list = config.read(args.filename)
    Files = os.listdir()

    dataformat = config["preprocessing"]["format"]
    dataYear = config["preprocessing"]["dataYear"]
    if dataformat == "csv":
        metadata = pd.read_excel(config["preprocessing"]["Filename"], sheet_name = "Informatie", index_col=1)
        LogReport("__"*80, 2)
        LogReport("# Metadata")
        LogReport(metadata.to_markdown())
    Inhabitants = int(config["locatie"]["aantal_bewoners"])
    Instance = config["model"]["instance"]
    transform = config["transform"]
    modules = config["modules"]
    TransformDataSelection = []
    Transform = []
    categoryweights = config["CategoryWeights"]
    categoryunits = config["CategoryUnits"]
    timeDivisionArray = []
    for i in categoryweights:
        frame = [i]
        [frame.append(float(j)) for j in categoryweights[i].split(",")]
        CategoryWeights.append(frame)

    for i in categoryunits:
        frame = [i]
        [frame.append(j) for j in categoryunits[i].split(",")]
        CategoryUnits.append(frame)

    LogReport("{}".format(CategoryUnits),3)
    LogReport("{}".format(CategoryWeights),3)


    for i in transform:
        LogReport("{} {}".format(i, transform[i]))
        TransformDataSelection.append(transform[i])
        Transform.append(i)

    if dataformat == "csv":
        data = pd.read_excel(config["preprocessing"]["Filename"], sheet_name = "Data", header=[0,1])
        data["DateTime"] = data[["Date","Time"]].apply(lambda x: str(x[0])[:10]+" "+str(x[1]), axis=1)
        data["DateTime"] = pd.to_datetime(data.DateTime, format="%Y-%m-%d %H:%M:%S")
        data["Datetime"] = data.loc[:, "DateTime"]#data[["DateTime"]]
        data = data.drop(["Date","Time"], axis=1)
        data = data.set_index("DateTime")
    elif dataformat == "linear":
        lineardata = pd.read_csv(config["preprocessing"]["Filename"]).fillna("None")
        lineardata["ID_Name_Property"] = lineardata["Productname"] + "_" + lineardata["Propertyname"]
        lineardata["DateTime"] = pd.to_datetime(lineardata.Timestamp, format="mixed")#%Y%m%d %H:%M:%S.%f")
        data = lineardata.drop(["Timestamp","Username","ProductID","Propertyname","Productname"],axis=1).set_index("DateTime")
        data = pd.pivot_table(data, index="DateTime",columns="ID_Name_Property", values="Value")
    CategoryUnits.append(["DateTime","YYYY-MM-DD HH:mm:ss+HH:mm","gebouwdata","Timezone DST aware datetime, laaatste HH:mm is afwijking van GMT"])

    if int(dataYear) > 0:
        data = data.loc[(data.index.year == datime.datetime.strptime(dataYear,"%Y").year)]

    MODULE = "dataCoverage"
    if modules[MODULE] == str(1):
        data = data.resample("1d").mean()
        data.to_csv("Raw_Export_{}.csv".format(Instance))
        logFigure("Raw_Data", data, Instance)
        dc = sns.heatmap(data, cmap=['r','y','g'], annot=True, fmt='.0f')
        dc.set_yticklabels(dc.get_yticklabels(), rotation=0, fontsize=8)
        plt.savefig("DataCoverage_{}.png".format(Instance))
        return data, Log, Instance

    LogReport("__"*80, 3)
    LogReport("## Index")
    LogReport(data.index)

    LogReport("__"*80, 3)
    LogReport("## Old Columns")
    LogReport(data.columns)

    LogReport("## Original Data")
    LogReport(data.describe().to_markdown())

    RenamedColumns = config["preprocessing"]["RenamedColumns"].split(",")
    LogReport(RenamedColumns)
    if RenamedColumns[0] == "help":
        for i in data.columns:
            LogReport(i)
        return data, Log, Instance
    elif RenamedColumns[0] == "transform":
        LogReport(TransformDataSelection)
        data = data[TransformDataSelection]
        data.columns = Transform
    else:
        data.columns = RenamedColumns
    data["hour"] = data.index.hour
    data["day"] = data.index.dayofyear
    CategoryUnits.append(["day","uren","KNMI","n.v.t. negeer deze kolom, niet timezone DST aware"])
    CategoryUnits.append(["hour","dagen","KNMI","n.v.t. negeer deze kolom, niet timezone DST aware"])
    LogReport("__"*80, 2)
    LogReport("## New Columns")
    LogReport(data.columns)

    Ts = [x for x in data.columns if "T" in x]
    Es = [x for x in data.columns if "E" in x]

    MODULE = "EtoP"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        Ps = [x.replace("E","P") for x in Es]
        for i, x in enumerate(Ps):
            CategoryWeights.append(DerivedCategory([Es[i]],x,copy.deepcopy(CategoryWeights))) # Copy E weights for Ps
            CategoryUnits.append([x,"kW", "berekend","{}".format(categoryunits[Es[i]].split(",")[-1].replace("energie","vermogen"))])

    LogReport("__"*80, 4)
    LogReport("## Isolating E and T columns and generating P names")
    LogReport(Ts)
    LogReport(Es)

    MODULE = "EtoP"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport(Ps)


    MODULE = "SanityCheckE"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        data[Es] = RepairCumulatives(data[Es])
        MODULE = "DHWUserProfile"
        if modules[MODULE] == str(1):
            data[["Vdhw"]] = RepairCumulatives(data[["Vdhw"]])

###############~~~~~~~~~~~~~~~~~~Milestone!
    data = data.resample(config["preprocessing"]["ResampleTime"]).mean().interpolate()
###############~~~~~~~~~~~~~~~~~~Milestone!

    MODULE = "EtoP"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        data[Ps] = data[Es].diff().bfill() #  energy to power
        timeDivisionArray.append(Es)


    data["dt"] = pd.to_numeric(data.index.to_series().diff().bfill())/(1000*1000*1000) #  dt
    CategoryWeights.append(["dt",0,0,0,1,0,0])
    CategoryUnits.append(["dt","s", "berekend","delta tijd, verschil tussen opvolgende tijdstappen"])
    data["DateTime"] = data.index


    if config["preprocessing"]["KNMI"] != "False":
        T_Columns = ["    Q","   RH"]
        ScaleArray = [100*100.,1.0] # scale J/cm2 to J/m2 and rain in 0.1mm to rain in mm
        RevertArray = []
        path = os.path.abspath(analysis.__file__)
        path = "".join(["/{}".format(i) for i in path.split("/")[:-1]])
        if config["preprocessing"]["KNMI"] == "True":
            try:
                KNMI = KNMI_Resampler(path+"/uurgeg_290_2011-2020.txt",T_Columns,ScaleArray,header=28, Interval = "30min")
                KNMI = KNMI.T[data.index].T#KNMI.index.year == int(config["schil"]["meetjaar"])]
            except KeyError:  #Attempt a newer KNMI Data file
                KNMI = KNMI_Resampler(path+"/uurgeg_290_2021-2025.txt",T_Columns,ScaleArray,header=28, Interval = "30min")
                KNMI = KNMI.T[data.index].T#KNMI.index.year == int(config["schil"]["meetjaar"])]
        else:
            KNMI = KNMI_Resampler(config["preprocessing"]["KNMI"],T_Columns,ScaleArray,header=28, Interval = "30min")
            KNMI = KNMI.T[data.index].T#KNMI.index.year == int(config["schil"]["meetjaar"])]
        data[["T-KNMI","P-sun","Dir","Wspd","Rf"]] = KNMI
        for i in ["T-KNMI","P-sun","Dir","Wspd","Rf"]:
            CategoryWeights.append(DerivedCategory(["Tamb"],i,copy.deepcopy(CategoryWeights)))
        CategoryUnits.append(["T-KNMI","°C", "KNMI","Tamb wordt vervangen door Tknmi wanneer niet realistisch is"])
        CategoryUnits.append(["P-sun","kW", "KNMI","P-sun wordt gebruikt voor Ga factor in RC en PVEfficiency"])
        CategoryUnits.append(["Dir","°", "KNMI","wordt niet gebruikt"])
        CategoryUnits.append(["Wspd","m/s", "KNMI","wordt niet gebruikt"])
        CategoryUnits.append(["Rf","mm/m2", "KNMI","wordt niet gebruikt"])
        timeDivisionArray.append("Rf")
        LogReport("__"*80, 4)
        LogReport("## Imported KNMI data for irradiation, wind, direction, temperature, rain")
        LogReport(KNMI.describe().to_markdown())
        logFigure("KNMI_Data_import", KNMI, Instance)

    MODULE = "SanityCheckTamb"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        data = SimilarityCheck(data, "Tamb", "T-KNMI", ULimit = 40.0, LLimit = -15.0, ROCLimit = 30.0/(12.0*60*60), VERBOSE = 10)
        logFigure("data_with_knmi", data, Instance)

    MODULE = "SanityCheckThese"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        data = SimilarityCheck(data, "Tamb", "T-KNMI", ULimit = 40.0, LLimit = -15.0, ROCLimit = 30.0/(12.0*60*60), VERBOSE = 10)
        logFigure("data_with_knmi", data, Instance)

    LogReport("__"*80, 4)
    LogReport("## Repaired cumulative trends, calculated power, calculted delta time")
    LogReport(data.describe().to_markdown())
    logFigure("Fixed_Data", data, Instance)

####~~~~~~~~~~~~~~~~~ USER ANALYSIS FUNCTION MAGIC ~~~~~~~~~~~~~~~~~####

    Function_List = getmembers(analysis, isfunction)
    if len(Function_List) > 0:
        data = AnalysisDealer(data,Function_List)

####~~~~~~~~~~~~~~~~~ USER ANALYSIS FUNCTION MAGIC ~~~~~~~~~~~~~~~~~####

    MODULE = "CalculateTavg"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        Indoor_temperatures = config["preprocessing"]["IndoorTemperatures"].split(",")
        data["Tavg"] = data[Indoor_temperatures].sum(axis=1)/3.0
        data["Tavg"]
        LogReport("__"*80, 4)
        LogReport("# Indoor temperatures compiled to average")
        LogReport(Indoor_temperatures)
        CategoryWeights.append(DerivedCategory(Indoor_temperatures,"Tavg",CategoryWeights))
        data["dT"] = data["Tavg"] - data["Tamb"]
        CategoryWeights.append(DerivedCategory(["Tavg","Tamb"],"dT",CategoryWeights))
        CategoryUnits.append(["Tavg","°C", "berekend","(Tlv+Tsk+Tzo)/3"])
        CategoryUnits.append(["dT","°C", "berekend","Tavg-Tamb"])

    MODULE = "DegreeDays"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        degreeDays_indoor = data["Tavg"].resample("1d").mean().interpolate().apply(lambda x: 18 - x if x > 18 else 0)
        ddi = degreeDays_indoor.sum()
        degreeDays_outdoor =  data["Tamb"].resample("1d").mean().interpolate().apply(lambda x: 18 - x if x > 18 else 0)
        ddo = degreeDays_outdoor.sum()
        degreeDays_delta_annemarie = (data["Tavg"] - data["Tamb"]).resample("1d").mean().interpolate()
        dda = degreeDays_delta_annemarie.sum()

    MODULE = "EventDetection"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        EventStudy = Eventor(data.loc[:, data.columns != 'DateTime'], VERBOSE=5)
        GenericConfig = config["eventdetection"]["GenericEvents"].split(",")
        if GenericConfig[3] == "None":
            GenericConfig[3] = None
        else:
            GenericConfig[3] = GenericConfig[3].split("_")
        if modules["GenericEvents"] == 1:
            EventStudy.GenericEvents(shortWindow = int(GenericConfig[0]), longWindow = int(GenericConfig[1]), sd =float(GenericConfig[2]), columns=GenericConfig[3])
            #EventStudy.EventCategorizer(CategoryWeights)

    MODULE = "ThermalBalance"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        ThermalColumns = config["preprocessing"]["ThermalColumns"].split(",")
        gas = int(config["schil"]["gas"])
        data = data.resample("30T").mean().interpolate()#.diff()#.plot()#.set_index("dT")[Es].plot()
        data["HeatInput"] = data[ThermalColumns].diff().sum(axis=1)
        CategoryWeights.append(DerivedCategory(ThermalColumns,"HeatInput",CategoryWeights, Verbose=3))
        data["DateTime"] = data.index
        if gas == 1:
            data["HeatInput"] = data["HeatInput"]*9.77
            CategoryUnits.append(["HeatInput","kW", "berekend","Gas*9.77 [m3] -> [kW]"])
        else:
            CategoryUnits.append(["HeatInput","kW", "berekend","SOM(Ecv1h,Ecv2h)"])


        LogReport("__"*80,5)
        LogReport("# Compiled thermal balance",3)
        LogReport(ThermalColumns)

    MODULE = "OpeningState"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        dwstateColumns = config["preprocessing"]["DoorWindowStates"].split(",")
        data["UAct"] = data[dwstateColumns].sum(axis=1)/len(dwstateColumns)
        CategoryWeights.append(DerivedCategory(dwstateColumns,"UAct",CategoryWeights))
        CategoryUnits.append(["UAct","n", "berekend","SOM(Sbd,Sra,Std)/3 dimensieloos"])
        LogReport("__"*80,5)
        LogReport("# Normalized door window states")
        LogReport(dwstateColumns)

    MODULE = "SolarPanelAnalysis"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        PVColumn = config["preprocessing"]["PVPanels"].split(",")
        PVArea = float(config["schil"]["pvoppervlak"])
        print(data[["P-sun"]])
        print(PVColumn)
        print(data[PVColumn])
        print(len(data[PVColumn]),len(data[["P-sun"]]))
        data["PVEfficiency"] = COP(data[PVColumn[0]]*1000, data["P-sun"]*PVArea).fillna(0)# can be re-used here.. basically simple efficiency calculation with error checking
        #data["COP"] = COP(data[HPTColumns].sum(axis=1), data[HPEColumns].sum(axis=1)).fillna(0.0)
        CategoryWeights.append(DerivedCategory(PVColumn,"P-sun",CategoryWeights))
        CategoryUnits.append(["P-sun","kW", "KNMI","P-sun wordt gebruikt voor Ga factor in RC en PVEfficiency"])
        LogReport("__"*80,1)
        LogReport("# Solar panel performance")
        LogReport(PVColumn)
        PVDC = data[["PVEfficiency"]].resample("1h").mean().interpolate().sort_values("PVEfficiency",ascending=False).reset_index(drop=True)
        pd.options.plotting.backend = "matplotlib"
        plt.clf()
        PVDC.plot(legend=True, lw=2)
        plt.savefig("Power_Duration_Curve_PV_{}.png".format(Instance))
        LogReport("\n\n ![Power_Duration_Curve_PV](Power_Duration_Curve_PV_{}.png)".format(Instance))
        LogReport(data[["PVEfficiency","P-sun"]+PVColumn].describe().to_markdown())

    MODULE = "EnergySignatureMethod"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        plt.clf()
        X = data[["dT"]].interpolate().bfill().ffill()
        y = data[["HeatInput"]]
        regressor = LinearRegression()
        regressor.fit(X, y)
        y_pred = regressor.predict(X)
        plt.rcParams['figure.figsize'] = 8., 4.
        plt.scatter(X, y, color = 'red')
        plt.plot(X, regressor.predict(X), color = 'blue')
        plt.title('Thermal Energy Signaturen(Pcv1h, Pcv0h)')
        plt.xlabel('Delta T [K] (Tin - Tavg)')
        plt.ylabel('Power [kW]')
        plt.savefig("Energy_signature_{}.png".format(Instance))

        LogReport("__"*80,1)
        LogReport("# Average method Heat loss coefficient")
        LogReport("The HLC (Heat loss coefficient, kW/K) is shown below. \n * The plot shows all datapoints, \n * the blue line denotes a linear interpolation. \n * The slope is the HLC \n * heat from occupants is not available \n * heat from internal dissipation is not added")
        LogReport(regressor.coef_[0][0] ,1)
        LogReport("\n\n ![energy Signature](Energy_signature_{}.png)".format(Instance))

    MODULE = "RCNetworkMethod"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        lambdaMap = {"Qtr": ["Tamb","Tavg","$U"],
                     "Qcv":["HeatInput"],
                     "Qsol":["P-sun","*Ag","$Ga"], # where Ag = glass area and Ga = solar irradiance factor, for solver!
                     "dTobj":["Qsol","Qcv","Qtr","dt","$C"],
                     "Tavg":["Tavg","dTobj"]}

        lambdaDict = {"Qtr": lambda Tamb, Tavg, U: (Tamb-Tavg)*0.001/ U,
                      "Qcv": lambda HeatInput: HeatInput,
                      "Qsol": lambda P_sun, Ag, Ga: P_sun*0.001*Ag*Ga,
                      "dTobj": lambda Qsol, Qcv, Qtr, dt, C: (Qtr+Qcv+Qsol)*dt/C,
                      "Tavg": lambda Tavg, dTobj: Tavg + dTobj}


        ThermallambdaMap = {"Qtr": ["Tamb","Tavg","$U"],
                            "HeatInput":["dT", "$C", "dt", "Qtr", "Qsol"],
                            "Qsol":["P-sun","*Ag","$Ga"], # where Ag = glass area and Ga = solar irradiance factor, for solver!
                            "dTobj":["dTobj"],
                            "Tavg":["Tavg","dTobj"]}

        ThermallambdaDict = {"Qtr": lambda Tamb, Tavg, U: (Tamb-Tavg)*0.001/ U,
                             "HeatInput": lambda dT, C, dt, Qtr, Qsol: ((dT*C/dt) - Qtr - Qsol)*0.001,
                             "Qsol": lambda P_sun, Ag, Ga: P_sun*0.001*Ag*Ga,
                             "dTobj": lambda dTobj: dTobj, # (Qtr+HeatInput+Qsol)*dt/C = dT,
                             "Tavg": lambda Tavg, dTobj: Tavg + dTobj}

        LogReport("## Energy HLC-Analysis",1)
        LogReport("__"*80,5)
        LogReport("Model - set of equations:")

        plt.clf()
        plt.cla()
        plt.close()
        for i in lambdaDict:
            tex = Lambda2Tex(lambdaDict[i])
            if OS == "Windows_NT":
                LogReport("\n {}".format(tex))
            else:
                try:
                    test = py2tex(tex,print_formula=False, print_latex=False, output="tex").replace("$","")
                    latex_to_img(test).save('{}.png'.format(i))
                    LogReport("\n ![{} term]({}.png)".format(i,i))
                except RuntimeError:
                    LogReport("\n {}".format(tex))

        fmf = MultiFitter(Instance,lambdaMap=lambdaMap,lambdaDict=lambdaDict,verbose=2) # On instantiation we MUST pass instance NAME
        fmf.loadData(data,initPredictors=True)
        fmf.loadConstants({"C":12000.0,"U":regressor.coef_[0][0],"Ag":float(config["schil"]["glasoppervlak"]),"Ga":0.3})
        fmf.loadConstants("best")
        df = pd.DataFrame(fmf.error,columns=["index","error","c0","c1"])
        fmf.dt = 1800.0


        MODULE = "FastSim"
        if modules[MODULE] == str(1):
            LogReport("Executing module {}".format(MODULE),5)
            logFigure("HLC_Analysis_Evolution_Inspired_Errors",pd.DataFrame(fmf.BulkEvolver("Tavg", constraints={"U":[0.01,1.5],"C":[1200.0,120000.0], "Ga":[0.0001,1.0]}, N = 20, repeats=3, Iterations=10),columns=["err","U","Ga","C"]), Instance)
        elif "{}.json".format(Instance) in Files:
            logFigure("HLC_Analysis_Evolution_Inspired_Errors",pd.DataFrame(fmf.BulkEvolver("Tavg", constraints={"U":[0.01,1.5],"C":[1200.0,120000.0], "Ga":[0.0001,1.0]}, N = 40, repeats=10, Iterations=100),columns=["err","U","Ga","C"]), Instance)
        else:
            logFigure("HLC_Analysis_Evolution_Inspired_Errors",pd.DataFrame(fmf.BulkEvolver("Tavg", constraints={"U":[0.01,1.5],"C":[1200.0,120000.0], "Ga":[0.0001,1.0]}, N = 4, repeats=100, Iterations=100),columns=["err","U","Ga","C"]), Instance)
        logFigure("Simulated_Errors_Parameters",pd.DataFrame(fmf.error,columns=["index","err","Tavg","Tavg_pr","U","Ag","Ga","C"]), Instance)

        LogReport("### Simulation with best parameters",4)
        Bestparams = fmf.constants
        for i in Bestparams:
            LogReport("{} : {}".format(i,Bestparams[i]),1)
        fmf.resetIndex()
        LogReport("-".format(i,Bestparams[i]),4)
        bestSimulation = pd.DataFrame(fmf.Simulate(steps=fmf.dataLength, err="Tavg")[-fmf.dataLength:],columns=["index","err","Tavg","Tavg_pr","U","Ag","Ga","C"])
        logFigure("Simulation with best parameters",bestSimulation, Instance,verbosityLimit=2)
        print(data["DateTime"])
        bestSimulation["DateTime"] = data.loc[:, "DateTime"]
        bestSimulation = bestSimulation.set_index("DateTime")


        MODULE = "RCReversePowerCurve"
        if modules[MODULE] == str(1):
            tp = MultiFitter(Instance,lambdaMap=ThermallambdaMap,lambdaDict=ThermallambdaDict,verbose=2)
            tp.loadData(data,initPredictors=True)
            tp.loadConstants("best")
            tp.dt = 1800.0
            PredictedThermal = pd.DataFrame(tp.Simulate(steps=tp.dataLength, err="HeatInput")[-tp.dataLength:],columns=["index","err","HeatInput","HeatInput_pr","U","Ag","Ga","C"])
            logFigure("Thermal prediction with best parameters",PredictedThermal, Instance, verbosityLimit=2)


        MODULE = "RCReversePowerCurve"
        if modules[MODULE] == str(1):
            PredictedThermal["DateTime"] = data.loc[:, "DateTime"]
            PredictedThermal = PredictedThermal.set_index("DateTime")

        print(len(data), len(bestSimulation))
        data.drop(data.tail(1).index,inplace=True)
        print(len(data), len(bestSimulation))

        data["simulation_Tavg_pr"] = bestSimulation["Tavg_pr"].values
        data["simulation_error"] = bestSimulation["err"].values
        CategoryUnits.append(["simulation_Tavg_pr","°C", "gesimuleerd/berekend","Tavg voorspelling volgens model"])
        CategoryUnits.append(["simulation_error","°C", "gesimuleerd/berekend","Error Tavg en Tavg_pr per tijdstap"])
        CategoryWeights.append(DerivedCategory(["Tavg"],"simulation_Tavg_pr",CategoryWeights))
        CategoryWeights.append(DerivedCategory(["Tavg"],"simulation_Tavg_pr",CategoryWeights))
        MODULE = "RCReversePowerCurve"
        if modules[MODULE] == str(1):
            data["simulation_HeatInput_pr"] = PredictedThermal["HeatInput_pr"].values
            CategoryUnits.append(["simulation_HeatInput_pr","kW", "gesimuleerd/berekend","Verwarmingsvermogen benodigd volgens model om Tavg te behalen"])
            CategoryWeights.append(DerivedCategory(["HeatInput"],"simulation_HeatInput_pr",CategoryWeights))

        # error function, returns simulation for n iterations and given parameters
        #logFigure("HLC_Analysis_Evolution_Inspired",pd.DataFrame(fmf.BulkError("Tavg", constraints={"U":[0.001,1.1],"C":[10000.0,12000.0]}, N = 3),columns=["err","U","C"]))

        # Evolution + gradient descent parameter search
        #logFigure("HLC_Analysis_Evolution_Inspired",pd.DataFrame(fmf.Evolver("Tavg", N=1000),columns=["index","err","Tavg","Tavg_pr","U","C"]))

        # Structured parameter search over defined bounds
        #logFigure("HLC_Analysis_Evolution_Inspired",pd.DataFrame(fmf.parameterSearchMap(err="Tavg", constraints={"U":[0.001,1.1],"C":[10000.0,12000.0]}),columns=["index","err","Tavg","Tavg_pr","U","C"]))


        fmf.plotError(All=True)
        for i in fmf.solveList:
            with open("Mufit_Error_{}.html".format(i), 'r', errors="ignore") as f:
                mufit_html = f.read()
            LogReport("__"*80, 2)
            LogReport("{} - index - error".format(i),1)
            if Verbosity > 1:
                Log += "\n" + mufit_html


    MODULE = "COP"
    if modules[MODULE] == str(1) and gas == 0:
        LogReport("Executing module {}".format(MODULE),5)
        HPEColumns = config["preprocessing"]["HeatPumpElectric"].split(",")
        HPTColumns = config["preprocessing"]["HeatPumpThermal"].split(",")
        data["COP"] = COP(data[HPTColumns].sum(axis=1), data[HPEColumns].sum(axis=1)).fillna(0.0)
        CategoryWeights.append(DerivedCategory(HPTColumns+HPEColumns,"COP",CategoryWeights))
        CategoryUnits.append(["COP","%", "berekend","SOM(Pcv1h,Pcv2h,Pcv1c,Pcv2c)/SOM(P1wp,P2wp)"])


        LogReport("__"*80,1)
        LogReport("# Coefficient Of Performance (COP) Analysis")
        LogReport("Statistics:")
        LogReport(data[["COP"]].describe().to_markdown())

        COPDC = data[["COP"]].resample("1h").mean().interpolate().sort_values("COP",ascending=False).reset_index(drop=True)
        pd.options.plotting.backend = "matplotlib"
        plt.clf()
        COPDC.plot(legend=True, lw=2, alpha=0.5)
        plt.savefig("Power_Duration_Curve_COP_{}.png".format(Instance))
        LogReport("\n\n ![Power_Duration_Curve_COP](Power_Duration_Curve_COP_{}.png)".format(Instance))
        LogReport(COPDC.describe().to_markdown())
        #logFigure("Interactive_pdc_curve",PDC)


# def readConfigLine(table,name):
#     line = config[table][name]
#     if line.split(",")


    MODULE = "ElectricUserProfile"
    if modules[MODULE] == str(1) and modules["ThermalBalance"] == 1:
        LogReport("Executing module {}".format(MODULE),5)
        pd.options.plotting.backend = "matplotlib"
        PPColumns = config["preprocessing"]["PositivePower"].split(",")
        NPColumns = config["preprocessing"]["NegativePower"].split(",")
        CategoryWeights.append(DerivedCategory(["dt"],"hour",copy.deepcopy(CategoryWeights)))
        CategoryWeights.append(DerivedCategory(["dt"],"day",copy.deepcopy(CategoryWeights)))
        CategoryUnits.append(["hour","uren", "berekend","n.v.t. negeer deze kolom, niet timezone DST aware"])
        CategoryUnits.append(["day","dagen", "berekend","n.v.t. negeer deze kolom, niet timezone DST aware"])

        data["Premainder"] = data[PPColumns].sum(axis=1) - data[NPColumns].sum(axis=1)
        CategoryWeights.append(DerivedCategory(PPColumns+NPColumns,"Premainder",CategoryWeights))
        CategoryUnits.append(["kW", "berekend","Q = m cp dt m* Vdhw * cp * (T2-T1)"])

        Epiv = pd.pivot_table(data, index=['hour'], columns=['day'], values=['Premainder'])
        Epiv = Epiv.loc[:, (Epiv != 0).any(axis=0)]
        Epiv.plot( color="g", title="Remainder Energy usage All days")

        E_Baseline = Epiv.mean(axis=1)
        E_Baseline.plot( color="r", lw=3)
        plt.savefig("Remainder_Energy_each_day_{}.png".format(Instance))
        plt.clf()
        E_Baseline.plot( color="r", lw=3, title="Average electricity profile")
        plt.savefig("Remainder_Electricity_Profile_{}.png".format(Instance))

        LogReport("__"*80, 1)
        LogReport("# User Behavior Analysis")

        LogReport("__"*80, 1)
        LogReport("## Electric baseline Analysis")
        LogReport("The electricity usage of the user is isolated.\n")
        LogReport("### Positive Power columns")
        LogReport(PPColumns)
        LogReport("### Negative Power columns")
        LogReport(NPColumns)
        LogReport("### Plots")
        LogReport("\n\n ![All days recorded](Remainder_Energy_each_day_{}.png)".format(Instance))
        LogReport("\n\n ![Remainder Average Electricity Profile](Remainder_Electricity_Profile_{}.png)".format(Instance))

    MODULE = "DHWUserProfile"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport("__"*80, 1)
        LogReport("## Domestic Hot Water")
        DHWColumns = config["preprocessing"]["DHWColumns"].split(",")
        # data["Pdhwcal"] = data.apply(PdTtoV, axis=1)
        year = data.index[0].year
        LogReport("Detected year: {}".format(year))
        LogReport("Date range summer:" + "{}-05-01".format(year)  + " _ {}-07-31".format(year))
        DHSummerSlice = data[ThermalColumns].loc["{}-05-01".format(year) : "{}-07-31".format(year)]
        data["Vdhwcal"] = data.apply(PdTtoV, T1=DHWColumns[0], T2=DHWColumns[1], Pdhw=DHWColumns[2], axis=1)  # good example of handling *args, we see mixed Pdhw and pd.DF.apply arguments
        data[["Vdhwcal"]].plot()
        data["Vdhwtheory"] = data[["Vdhwcal"]].apply(PandasDHWWrapper, Inhabitants=Inhabitants, axis=1)  # Needs a series to work. Does not matter which one.
        CategoryWeights.append(DerivedCategory(DHWColumns,"Vdhwcal",CategoryWeights))
        CategoryWeights.append(DerivedCategory(["Vdhwcal"],"Vdhwtheory",copy.deepcopy(CategoryWeights)))
        CategoryUnits.append(["Vdhwcal","kW", "berekend","Q = m cp dt m* Vdhw * cp * (T2-T1)"])
        CategoryUnits.append(["Pdhw","kW", "berekend","Q = m cp dt m* Vdhw * cp * (T2-T1)"])


        MODULE = "DHWDataDriven"
        if modules[MODULE] == str(1):
            LogReport("Executing module {}".format(MODULE),5)
            SummerDetection = pd.pivot_table(data, index=["hour"], columns=["day"], values= ThermalColumns) # DHSummerSlice[]
            plt.clf()
            SummerDetection.plot( color="g", title="warm water usage > 0 taken from summer period")
            LogReport("### Summer detection DHW")
            LogReport(SummerDetection.to_markdown())
            LogReport(SummerDetection.describe().to_markdown())

        piv = pd.pivot_table(data, index=['hour'], columns=['day'], values=['Vdhwcal'])
        piv2 = piv.loc[:, (piv != 0).any(axis=0)]
        #plt.clf()
        pd.options.plotting.backend = "matplotlib"
        piv.plot(color="g", title="All days with warm water usage > 0 and average of those")
        DHW_Baseline = piv.mean(axis=1)
        DHW_Baseline.plot( color="r", lw=3)
        plt.plot(dhw[Inhabitants-1][0], dhw[Inhabitants-1][1], color="b", lw=2)
        plt.savefig("Remainder_DHW_each_day_{}.png".format(Instance))
        LogReport("\n\n ![All DHW days recorded](Remainder_DHW_each_day_{}.png)".format(Instance))

        plt.clf()
        DHW_Baseline.plot( color="r", lw=3)
        plt.plot(dhw[Inhabitants-1][0], dhw[Inhabitants-1][1], color="b", lw=2)
        plt.savefig("User_profile_theory_DHW_{}.png".format(Instance))

        LogReport("Baseline: {:2.4f} m3, theory: {:2.4f} m3, deviation: {:2.2f}%, Difference: {:2.4f} m3".format(DHW_Baseline.sum(),sum(dhw[Inhabitants-1][1]),(DHW_Baseline.sum()/sum(dhw[Inhabitants-1][1]))*100, DHW_Baseline.sum()-sum(dhw[Inhabitants-1][1])))
        LogReport(DHW_Baseline.describe().to_markdown())
        LogReport("\n\n ![User profile compared to empirical model](User_profile_theory_DHW_{}.png)".format(Instance))
        Ps.append("Premainder")
        Ps.append("Pdhw")
    MODULE = "BalanceDurationCurve"
    if modules[MODULE] == str(1) and modules["ThermalBalance"] == 1:
        LogReport("Executing module {}".format(MODULE),5)
        # this generates a power duration curve
        pd.options.plotting.backend = "plotly"
        LogReport("__"*80)
        LogReport("## Duration Curves")
        LogReport("* Power")
        LogReport(" * {}".format(Ps))
        #data[Ps].plot()
        PDC = data["Premainder"].resample("1h").mean().interpolate().sort_values("Premainder",ascending=False).reset_index(drop=True)
        pd.options.plotting.backend = "matplotlib"
        plt.clf()
        PDC.plot(legend=True, lw=2, alpha=0.5)
        plt.savefig("Power_Duration_Curve_sorted_on_balance_{}.png".format(Instance))
        LogReport("\n\n ![Power_Duration_Curve_sorted_on_balance](Power_Duration_Curve_sorted_on_balance_{}.png)".format(Instance))
        LogReport(PDC.describe().to_markdown())
        #logFigure("Interactive_pdc_curve",PDC)
    MODULE = "TemperatureDurationCurve"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport("__"*80)
        LogReport("* Temperature")
        Ts.append("Tavg")
        Ts.append("dT")
        TDC = data[Ts].resample("1h").mean().interpolate().sort_values("dT",ascending=False).reset_index(drop=True)
        pd.options.plotting.backend = "matplotlib"
        plt.clf()
        TDC.plot(legend=True, lw=2, alpha=0.5)
        plt.savefig("Temperature_Duration_Curve_sorted_on_balance_{}.png".format(Instance))
        LogReport("\n\n ![Temperature_Duration_Curve_sorted_on_balance](Temperature_Duration_Curve_sorted_on_balance_{}.png)".format(Instance))
        LogReport(TDC.describe().to_markdown())

    MODULE = "GenericEvents"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport("# Event detection")
        EventStudy = Eventor(data.loc[:, data.columns != 'DateTime'])
        # Fetch all config
        GenericConfig = config["eventdetection"]["GenericEvents"].split(",")
        if GenericConfig[3] == "None":
            GenericConfig[3] = None
        else:
            GenericConfig[3] = GenericConfig[3].split("_")
        EventStudy.GenericEvents(shortWindow = int(GenericConfig[0]), longWindow = int(GenericConfig[1]), sd =float(GenericConfig[2]), columns=GenericConfig[3])
        LogReport("## Generic event detection:")
        LogReport("* Short window: {} h".format(GenericConfig[0]))
        LogReport("* Long window: {} h".format(GenericConfig[1]))
        LogReport("* Standard deviation exceedance: {}".format(GenericConfig[2]))
        LogReport("* Columns: {} (if None, all data will be scanned for events)".format(GenericConfig[3]))
        LogReport("* Event columns:")
        LogReport("{}".format(EventStudy.eventcolumns))

        NormalizedEvents = EventStudy.EventIndicer(threshold=float(config["eventdetection"]["NormalizedEvents"]))
        LogReport("\n## Normalized event detection:")
        LogReport("* Standard deviation exceedance: {}".format(config["eventdetection"]["NormalizedEvents"]))
        LogReport("* Detected events: {}".format(len(NormalizedEvents)))
        for i in NormalizedEvents:
            LogReport(i)
            VisualizeEvent(data, i, Instance, columns = ["Tavg", "Tamb", "dT", "Ppv"], Size=[10,8])
            LogReport("\n ![event_{}](event_{}.png)".format(i["Event"], i["Event"]))

        MODULE = "OtherEventDetectors"
        if modules[MODULE] == str(1):
            LogReport("Executing module {}".format(MODULE),5)
            cEventCfg = config["eventdetection"]["OtherEvents"].split(",")  # CustomEventConfig
            Events = []
            for i in cEventCfg:
                EventConfig = config["eventdetection"][i].split(",")
                LogReport("__"*80, 2)
                LogReport("## Custom {} trend {}".format(i, EventConfig[1]))
                LogReport("* Standard deviation exceedance: {}".format(EventConfig[0]))
                Events.append(EventStudy.EventIndicer(threshold=float(EventConfig[0]), trend=EventConfig[1]))
                LogReport("* Detected events: {}".format(len(Events[-1])))
                for j in Events[-1]:
                    LogReport("* {}".format(j))
                    VisualizeEvent(data, j, Instance, columns=["Tavg", "Tamb", "dT", "Ppv"], Size=[10,8])
                    LogReport("\n ![event_{}](event_{}.png)".format(j["Event"], j["Event"]))

        pd.options.plotting.backend = "plotly"
        figname = '{}_data_processed'.format(config["preprocessing"]["Filename"].split(".")[0])
        EventData = EventStudy.data[EventStudy.eventcolumns]
        EventData.to_csv("{}_Events_Export.csv".format(Instance))
        LogReport("__"*80, 2)
        LogReport("## Plotly Interactive Events")
        LogReport(EventData.describe().to_markdown())
        logFigure("Event_Detections", EventData, Instance)
        LogReport("__"*80, 1)
        LogReport("# Plotly Interactive All processed data")
        LogReport(data.describe().to_markdown())
        logFigure(figname, data, Instance)

    MODULE = "ColumnCategorization"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport("__"*80, 2)
        LogReport("# Final Sub-categorization")
        Finalcategories = pd.DataFrame(CategoryWeights[1:],columns=CategoryWeights[0], index=[i[0] for i in CategoryWeights[1:]]).drop("Combined_Categories",axis=1)
        Finalcategories.to_csv("{}_categories_Export.csv".format(Instance))
        LogReport(Finalcategories.to_markdown())
        logFigure("Final_Categories", Finalcategories, Instance, kind="bar")


    MODULE = "DataExport"
    if modules[MODULE] == str(1):
        LogReport("Executing module {}".format(MODULE),5)
        LogReport("__"*80, 2)
        print("Exporting data as data_export_{}.csv".format(Instance))
        try:
            data.index = data.index.tz_localize("Europe/Amsterdam",nonexistent="shift_forward", ambiguous="infer")
        except pytz.exceptions.AmbiguousTimeError:
            data.index = data.index.tz_localize("Europe/Amsterdam",nonexistent="shift_forward", ambiguous="NaT")
        data.to_csv("data_export_{}.csv".format(Instance))

        dataHourly = TimeDivision(data,timeDivisionArray)
        dataHourly = dataHourly.resample("1h").mean()
        dataHourly = TimeDivision(dataHourly,timeDivisionArray, reverse=True)
        dataHourly['DateTime'] = dataHourly['DateTime'].astype(str).str[:-6]
        dataHourly.to_csv("data_export_{}_hourly.csv".format(Instance))

        dataDaily = TimeDivision(data,timeDivisionArray)
        dataDaily = dataDaily.resample("1D").mean()
        dataDaily = TimeDivision(dataDaily,timeDivisionArray, reverse=True)
        dataDaily['DateTime'] = dataDaily['DateTime'].astype(str).str[:-6]
        dataDaily.to_csv("data_export_{}_daily.csv".format(Instance))

        dataWeekly = TimeDivision(data,timeDivisionArray)
        dataWeekly = dataWeekly.resample("1W").mean()
        dataWeekly = TimeDivision(dataWeekly,timeDivisionArray, reverse=True)
        dataWeekly['DateTime'] = dataWeekly['DateTime'].astype(str).str[:-6]
        dataWeekly.to_csv("data_export_{}_weekly.csv".format(Instance))

        dataMonthly = TimeDivision(data,timeDivisionArray)
        dataMonthly = dataMonthly.resample("M").mean()
        dataMonthly = TimeDivision(dataMonthly,timeDivisionArray, reverse=True)
        dataMonthly['DateTime'] = dataMonthly['DateTime'].astype(str).str[:-6]
        dataMonthly.to_csv("data_export_{}_monthly.csv".format(Instance))

        dataMorning = TimeDivision(dataHourly,timeDivisionArray)
        dataMorning = dataMorning.between_time("8:00", "13:00")
        dataMorning['DateTime'] = dataMorning['DateTime'].astype(str).str[:-6]
        dataMorning.to_csv("data_export_{}_morning.csv".format(Instance))

        dataAfternoon = TimeDivision(dataHourly,timeDivisionArray)
        dataAfternoon = dataAfternoon.between_time("13:00", "18:00")
        dataAfternoon['DateTime'] = dataAfternoon['DateTime'].astype(str).str[:-6]
        dataAfternoon.to_csv("data_export_{}_afternoon.csv".format(Instance))

        dataEvening = TimeDivision(dataHourly,timeDivisionArray)
        dataEvening = dataEvening.between_time("18:00", "23:00")
        dataEvening['DateTime'] = dataEvening['DateTime'].astype(str).str[:-6]
        dataEvening.to_csv("data_export_{}_evening.csv".format(Instance))

        dataNight = TimeDivision(dataHourly,timeDivisionArray)
        dataNight = dataNight.between_time("23:00", "8:00")
        dataNight['DateTime'] = dataNight['DateTime'].astype(str).str[:-6]
        dataNight.to_csv("data_export_{}_night.csv".format(Instance))

    LogReport(pd.DataFrame(CategoryUnits).to_markdown(),1)
    Log = Headers + "__"*100 + Log
    return data, Log, Instance

def main():
    return ProcessData()

if __name__ == "__main__":
    print("preProcessor is being run directly")
    ProcessData()
else:
    print("preProcessor is being imported")
