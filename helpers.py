import pandas as pd
import seeq.spy as spy
import matplotlib.pyplot as plt
import numpy as np

# function to calculate number of null (consecutive) groups and time between groups 

def time_between_null_groups(series, time_column=None):
    """
    Calculates the time difference between groups of consecutive null values in a pandas Series.

    Args:
    series (pd.Series): The pandas Series containing potential null values.
    time_column (str, optional): The name of the time column if the series is part of a DataFrame. If None,
    the index of the series is assumed to be the time. Defaults to None.

    Returns:
    tuple: A tuple containing:
    - pd.Series: A Series containing the time differences between null groups. 
    Returns an empty series if no null groups are found.
    - int: The number of null groups found in the series.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("Input must be a pandas Series.")

    if series.isnull().sum() == 0:
        return pd.Series([], dtype='timedelta64[ns]'), 0

    null_groups = series.isnull().astype(int).groupby((series.isnull() != series.isnull().shift()).cumsum())

    null_group_indices = []
    for name, group in null_groups:
        if group.iloc[0] == 1:  # Check if it's a null group
            null_group_indices.append(group.index)

    num_null_groups = len(null_group_indices)

    if num_null_groups < 2:
        return pd.Series([], dtype='timedelta64[ns]'), num_null_groups

    time_differences = []
    for i in range(num_null_groups - 1):
        end_of_current_group = null_group_indices[i][-1]
        start_of_next_group = null_group_indices[i + 1][0]

        if time_column:
            time_difference = series.index.get_level_values(time_column)[start_of_next_group] - series.index.get_level_values(time_column)[end_of_current_group]
        else:
            time_difference = start_of_next_group - end_of_current_group
        
        time_differences.append(time_difference)
    
    return pd.Series(time_differences), num_null_groups


def eval_failures(tag, start_date, end_date, sampling_rate):
    """
    Calculates number of failures defined by consecutive null values (ie x consecutive days of null values is 1 failure)

    Args:
    tag (str): instrument tag number, must be valid seeq tag
    start_date (str): start date for analysis in format 
    end_date (str): 
    sampling_rate (str):

    Returns:
    TODO
    """
    # get data from seeq
    results = spy.search({'Name': tag}, quiet=True)
    results = results[results['Name']==tag]
    data=spy.pull(results.iloc[0], start=start_date, end=end_date, header='Name', quiet=True)#, header='ID')

    # resample to  filter out small blips
    sampling_avg = data.resample(sampling_rate).mean()

    # plot the filtered averages
    rows_with_nan = sampling_avg[sampling_avg.isnull().any(axis=1)]
    rows_with_nan = rows_with_nan.fillna(-100)
    rows_with_nan = rows_with_nan.reset_index()
    fig, ax = plt.subplots()
    sampling_avg.plot(ax=ax)
    rows_with_nan.plot.scatter(x='index', y=tag, ax=ax, color='red')
    
    plt.savefig(tag)

    # calculate the number of failures and average time between failures
    time_bw_fail = time_between_null_groups(pd.Series(sampling_avg[tag]))
    num_days = time_bw_fail[0] / np.timedelta64(1, 'D')
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Calculate the difference in years
    years_difference = (end_date - start_date) / pd.Timedelta(days=365.25)
    
    #need to troubleshoot:
    #print('For tag {} there are {} failures in {:.1f} years with average time between failures of {:.1f} days'.format(tag,time_bw_fail[1], years_difference, num_days[0]))
    # print('For tag {} there are {} failures in {:.1f} years'.format(tag,time_bw_fail[1], years_difference))

    return (time_bw_fail[1], years_difference)