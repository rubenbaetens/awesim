# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 21:36:52 2012

@author: RDC
"""

import numpy as np
#import os
#import scipy.io
#import re
import copy
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
#import cPickle as pickle
#import bisect
#import tables as tbl
from datetime import datetime, timedelta
from .utilities import aggregate_by_time, make_datetimeindex, aggregate_dataframe
import pandas as pd
import pdb
import pickle


class Result(object):
    """
    Class containing the result for one single variable but for different 
    simulations.  An instance from this class is returned from Simdex.get()
    
    This class also contains the plot functionality and methods to apply 
    basic operations and functions to it. 
    """
    
    def __init__(self, values, time=None, identifiers=None, **kwargs):
        """
        Instantiate a Result object. 
        
        Variables
        ---------
        
        values = dictionary {sid:values}
        time (optional) = dictionary {sid:time}
        identifiers (optional) = dictionary {sid:identifier}
        **kwargs are converted into attributes.  This is useful to pass eg. the 
        year for the data (use for example year=2010)
        
        """
        
        self.val = values
        if time is not None:
            self.time = time
            self.time4plots = {}
        if identifiers is not None:
            self.identifiers = identifiers
        self.simulations = sorted(self.val.keys())
        
        for k,v in kwargs.items():
            setattr(self, k, v)

    def save(self, filename):
        """
        save(filename)
        
        Save the Simdex object by pickling it with cPickle
        
        To unpickle (= load) use the following command:
            objectname = pickle.load(open(filename,'rb'))
            # 'rb' stands for 'read, binary'
            
        """
        
        f = file(filename,'wb') 
        # wb stands for 'write, binary'
        pickle.dump(self, f)
        f.close()
        
        return filename + ' created'
            
    def values(self):
        """
        Return a list with as elements, the values of the variable in the order 
        of the sid's
        
        It does not seem a good idea to return an array by default, cause the 
        variables for different SID's can have different lengths. 
        Exception: when the length of each of the variables is 1, a reshaped 
        array is returned.
        
        If a value in a single length array is None, it is replaced by NaN in the
        returned array.
        """
        
        result = [self.val[sid] for sid in self.simulations]
        
        lengths=[]
        for i,x in enumerate(result):
            try:
                l = len(x)
            except TypeError:
                # x is a value, it is a numpy.float64, so length=1
                if x is None:
                    result[i]=np.NaN
                l = 1
            lengths.append(l)
                    
        ls = np.array(lengths)
        
        if np.all(ls==1):
            return np.array(result).reshape(len(ls))
        else:
            return result
        
    def trapz(self):
        """
        Integrate the values(time) using the composite trapezoidal rule
        Returns an array with the integrated values, in sorted order
        """
        
        if not hasattr(self, 'time'):
            raise AttributeError("This Result object has no attribute 'time'")
        
        result = []
        for sid in self.simulations:
            result.append(np.trapz(self.val[sid], x=self.time[sid]))
        
        return np.array(result)
        

    def aggregate(self, period=86400, interval=3600, label='middle'):
        """
        Calculate the aggregated average of the timeseries by 
        period (typical a day) in bins of interval seconds (default = 3600s).
        
        label = 'left', 'middle' or 'right'.  
        'Left' means that the label i contains data from 
        i till i+1, 'right' means that label i contains data from i-1 till i.    
        
        Returns a dataframe with period/interval values, one for each interval
        of the period. 
        
        A few limitations of the method:
            - the period has to be a multiple of the interval
            - for correct results, the timespan of the timeseries has to be a 
              multiple of the period
                
        Example of usefulness: if the timeseries has 15-minute values for 1 year of
        eg. the electricity consumption of a building.  
        - You want to know how a typical daily profile looks like, by 15 minutes 
          ==> period=86400, interval=900
        - you want to know how a typical weekly profile looks like, by hour:
          ==> period = 7*86400, interval=3600
        
        Changelog:
            - 20121113: split the method because to_dataframe() does NOT 
                        work with events if there are multiple sid's in the
                        result.  
        """
        
        # check existence of attributes
        if not hasattr(self, 'year'):
            print 'We suppose the data is for 2011'
            self.year=2011
        
        #pdb.set_trace()
        for i, sid in enumerate(sorted(self.val.keys())):
            agg_array = aggregate_by_time(self.val[sid], self.time[sid], period, interval)
            if not len(agg_array) == int(period/interval):
                raise NotImplementedError("This will not work: there are no values at the interval timestaps for %s" % (sid))
            if i==0:
                agg_array_all = copy.deepcopy(agg_array)
            else:
                agg_array_all = np.column_stack((agg_array_all, agg_array))
        
        if label == 'left':
            index = make_datetimeindex(np.arange(0, period, interval), self.year)
        elif label == 'right':
            index = make_datetimeindex(np.arange(interval, period+interval, interval), self.year)
        elif label == 'middle':
            index = make_datetimeindex(np.arange(0+interval/2., period+interval/2., interval), self.year)
        
        df_agg = pd.DataFrame(data=agg_array_all, index=index, 
                              columns=sorted(self.val.keys()))        
        return df_agg
        
        

    def smooth(self, interval=300):
        """
        Calculate the running average of a timeseries
        
        Parameters
        ----------
        interval: interval for the running average, in seconds (default = 300s)
        
        Returns
        -------
        
        returns a result object with smoothened values and adapted time
        """
        
        def smooth_by_time(signal, time, interval=300, label='left'):
            """
            Function to calculate the running average of a timeseries 
            in bins of interval seconds (default = 300s).
            
            """
            #pdb.set_trace()
            ratio = interval/(time[1]-time[0])
            
            time = np.arange(0, time[-1]+interval, interval)
            
            data = np.zeros(len(time))
            data[0] = signal[0]
            for i in range(1,len(data)):
                data[i]=np.mean(signal[((i-1)*ratio):(i*ratio)])
                
            return data, time       
    
        value = {}
        time = {}
        for sid in self.simulations:
            value[sid], time[sid] = smooth_by_time(signal=self.val[sid], time=self.time[sid], interval=interval)

        result = Result(values=value, time=time)
        
        return result


    def to_dataframe(self):
        """
        Return a pandas dataframe from this result
        Attention: this method does NOT work if res contains multiple
        SID's who contain events (duplicate index values).  
        This case is roughly detected by checking the resulting df length.
    
        """
        # pdb.set_trace()
        # check existence of attributes
        if not hasattr(self, 'year'):
            print 'We suppose the data is for 2011'
            self.year=2011

        for i, sid in enumerate(sorted(self.val.keys())):
            # create a df from this single 'column'
            index = make_datetimeindex(self.time[sid], self.year)
            if i==0:
                df = pd.DataFrame(data=self.val[sid], index=index, columns=[sid])
            else:
                df_right = pd.DataFrame(data=self.val[sid], index=index, columns=[sid])
                df = df.join(df_right, how='outer', sort=True)


        if len(df) > len(self.val) * max([len(self.val[sid]) for sid in self.val]):
            raise NotImplementedError("The result contains multiple SID's and events.  Pandas cannot join() these type of dataframes (yet)" )
        return df
            



    def plot(self, ylabel=None):
        """
        Creates a matplotlib figure with a simple plot of the timeseries for 
        each of the simulations in self.val
        
        A string can be passed (ylabel) that will be used to label the y-axis
        """
        
        # In order to plot the timeseries nicely with dates, we use plot_date()
        def create_time4plot(sid):
            """Convert time into matplotlib format"""
            start = datetime(self.year, 1, 1)
            datetimes = [start + timedelta(t/86400.) for t in self.time[sid]]
            self.time4plots[sid] = date2num(datetimes)
            

       
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.hold = True        

        # we have to make a distinction between plotting timeseries and other results
        try:
            if len(self.time[self.simulations[0]])==len(self.val[self.simulations[0]]): 
                plot_type='plot_date'
            elif len(self.val[self.simulations[0]]) <> 1:
                # most probably an aggregated array. So plot the x values for 
                # each SID as a series 
                plot_type='aggregated'
            else:
                # length == 1, so single_value
                plot_type = 'single_value'
        except:
            try:
                if len(self.val[self.simulations[0]]) <> 1:          
                    # most probably an aggregated array. So plot the x values for 
                    # each SID as a series 
                    plot_type='aggregated'
                else:
                    # length == 1, so single_value
                    plot_type = 'single_value'
            except:
                # I get an exception when trying to get the length of a single
                # intgegrated value
                plot_type = 'single_value'
                
        if plot_type=='plot_date':
            for sid in self.simulations:
                try:
                    label = self.identifiers[sid]
                except KeyError:
                    label=sid
                if not self.time4plots.has_key(sid):
                    create_time4plot(sid)
                    
                ax.plot_date(self.time4plots[sid], self.val[sid], fmt='', ls = '-', 
                             label=label)            
        elif plot_type == 'single_value':
            ax.plot(range(len(self.simulations)), self.values(), 'D')
            ax.set_xticks(range(len(self.simulations)))
            ticklabels = [self.identifiers[sid] for sid in self.simulations]
            ax.set_xticklabels(ticklabels)
        else:
            # aggregated, plot lines with markers            
            for sid in self.simulations:
                try:
                    label = self.identifiers[sid]
                except KeyError:
                    label=sid
                
                ax.plot(self.val[sid], 'o-', label=label)            
                             
        leg = ax.legend(loc='best')
        lines = ax.get_lines()
        if plot_type == 'plot_date':
            ax.set_xlabel('time')
        ax.set_ylabel(ylabel)
        plt.grid()
        
        return [fig, lines, leg]
            
        
