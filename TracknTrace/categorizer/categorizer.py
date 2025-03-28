import pandas as pd
import argparse
import configparser

pd.options.plotting.backend = "plotly"
pd.options.mode.chained_assignment = None

def EventCategorizerFcn(categories, data, cats, target): # list, data, df
    """Creates map of category:data and sums results per category

    @param categories  data column: category translation pairs
    @param data  original data to categorize
    @param cats  Scaling of detected event
    @param target  The target trends in data to dp event categorization on.

    @return df  dataframe which dumps original data and replaces with event detections for target"""
    df = pd.DataFrame(columns = categories[0][1:], index = data.index)
    df =  df.fillna(0.0)
    print(df)
    TargetOrigin = target.split("_")[1]
    for i in data[[target]].T:
        #print(i, data[[target]].T[i], float(data[[target]].T[i])*cats.loc[TargetOrigin])
        df.T[i] += float(data[[target]].T[i].iloc[0])*cats.loc[TargetOrigin]# ## $ FINALLY TYHIS DOESD OETGIOGFEIHAOFAWIO{WFG
    return df

def DoAllCategories(categories, data, cats, ScanList = None): # list, data, df
    """Creates map of category:data and sums results per category for all data

    @param categories  data column: category translation pairs
    @param data  original data to categorize
    @param cats  Scaling of detected event

    @return df  dataframe which dumps original data and replaces with event detections for all data"""
    df = pd.DataFrame(columns = categories[0], index = data.index)
    df =  df.fillna(0.0)
    print(df)
    progress = len(data.columns)
    for z,j in enumerate(data.columns):
        print("doing {}, {}%".format(j,(z/progress)*100))
        try:
            if j != "normevents":
                TargetOrigin = j.split("_")[1]
                if ScanList is None or TargetOrigin in ScanList:
                    for i in data[[j]].T:

                        #df.T[i] += abs(float(data[[j]].T[i].iloc[0]))*cats.loc[TargetOrigin]# ## $ FINALLY TYHIS DOESD OETGIOGFEIHAOFAWIO{WFG
                        #print("Transponate:",df.T[i])
                        #print("loc:",df.loc[i,])
                        #print(df.T[i])
                        df.loc[i] = df.loc[i,] + abs(float(data[[j]].loc[i,].iloc[0]))*cats.loc[TargetOrigin]
                        #print(i, data[[j]].loc[i,], float(data[[j]].loc[i,].iloc[0])*cats.loc[TargetOrigin], df.loc[i])
        except KeyError:
            print("{} does not exist".format(j))
    return df

parser = argparse.ArgumentParser()
parser.add_argument("instance", type=str,
                    help="Input Instance")
args = parser.parse_args()


EventData = pd.read_csv("{}_Events_Export.csv".format(args.instance))
EventData.set_index("DateTime", inplace=True)

Finalcategories = pd.read_csv("{}_categories_Export.csv".format(args.instance))
Finalcategories.set_index("Unnamed: 0", inplace=True)


print(EventData.describe())
print(EventData)

print(Finalcategories.describe())
print(Finalcategories)

print([list(Finalcategories),Finalcategories.values.tolist()])

print("lets try to do the work!")

print(Finalcategories.index)

config = configparser.ConfigParser()
config.optionxform = lambda option: option
result_list = config.read("{}.metadata".format(args.instance))
Scanlist = config["eventdetection"]["Scanlist"].split(",")
print("Items included in performance gap scan: {}".format(Scanlist))

#df = EventCategorizerFcn([list(Finalcategories),Finalcategories.values.tolist()], EventData, Finalcategories, "event_Sbd_sw_24_1.2")
df = DoAllCategories([list(Finalcategories),Finalcategories.values.tolist()], EventData, Finalcategories, ScanList = Scanlist)

print(df)

fig = df.plot()
fig.write_html("{}_FinalCategories.html".format(args.instance), auto_open=True)
dfnorm = df/df.max()

fig = dfnorm.plot()
fig.write_html("{}_FinalCategories_normalized.html".format(args.instance), auto_open=True)
