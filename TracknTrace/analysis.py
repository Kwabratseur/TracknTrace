import pandas as pd

# def skeleton(data,Log):
#     data["new_column"] = (data["a"] * data["b"] / data["c"] - data["e"] + data["d"].sum())
#     Log += "\n## Did something\n A*B/(C - E) + sum(D), cool\n\n"
#     columns = ["new_column"]
#     return data, Log, columns

def DegreeDays(data,Log):
    """! Calculate Degreedays based on outside temperature and livingroom temperature

    @param data  Standardized input (pandas)dataframe. It's content can be derived from <input_data>.metadata
    @param Log  This Log will be compiled to .html, you can add results to this.

    @return data     A new dataframe with the applied transformations
    @return Log      The log with new entries
    @return columns  New columns added to the dataframe
    """
    data["DegreeDays"] = (data["Tlv"] - data["Tamb"]).resample("1d").mean().interpolate()
    Log += "\n## Added livingroom degree-days\n Tlv - Tamb \n---------------------------\n"
    columns = ["DegreeDays"]
    return data, Log, columns
