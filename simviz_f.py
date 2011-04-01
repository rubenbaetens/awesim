# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 09:48:35 2011

@author: RBa
"""

__author__ = "Ruben Baetens"
__version__ = "0.0.1"

import matplotlib.pyplot as plt
import numpy as np
import re
import mpl_toolkits.axisartist as AA

from buiuser import *
from mpl_toolkits.axes_grid1 import make_axes_locatable
from simman import Simulation

def plt_comfort(self):
    """
    plt_comfort(self)
        
    plot a graphical unit of the indoor temperatures of #zones
    - self = simman.Simulation-object
    """

    # now get the data of the zone temperatures
    time = self.get_value(u'Time')

    # now get the data of the outdoor temperature and also smoothen them
    dickie = self.exist(u'sim.Te')
    outdoor = self.get_value(dickie[-1]) - 273.15
    time_s, outdoor_s = get_smoothened_data(outdoor_orig, time, 86400, 'to_file')
            
    # now get the data of the zone temperatures
    dickie = self.exist(u'summary.Top')
    temps = np.zeros((len(time),len(dickie)))
    for colum in range(len(dickie)):            
        temps[:,colum] = self.get_value(dickie[colum])
    temps = temps - 273.15

    # now get the statistical data of the temperatures ...
    med, pstd, mstd, pppstd, mmmstd = get_stdev(time, temps)
    # ... smoothen them to hourly values ...
    time_h, outdoor = get_smoothened_data(outdoor, time, 3600, 'to_file')
    time_h, med = get_smoothened_data(med, time, 3600, 'to_file')
    time_h, pstd = get_smoothened_data(pstd, time, 3600, 'to_file')
    time_h, mstd = get_smoothened_data(mstd, time, 3600, 'to_file')
    time_h, pppstd = get_smoothened_data(pppstd, time, 3600, 'to_file')
    time_h, mmmstd = get_smoothened_data(mmmstd, time, 3600, 'to_file')
    # ... and save them in an array p1
    p1 = [time_h, outdoor, med, pstd, mstd, pppstd, mmmstd]

    # ... smoothen them to daily basis
    t_colum = temps[:,0]
    to_time, t_colum = get_smoothened_data(t_colum, time_s, 86400, 'to_file')
    smoothened_temps = np.array(t_colum)
    for i in range(1,len(dickie)):            
        t_colum = temps[:,i]
        to_time, t_colum = get_smoothened_data(t_colum, time_s, 86400, 'to_file')
        smoothened_temps = np.vstack((smoothened_temps, t_colum))
    smoothened_temps = smoothened_temps.T
    # now get the statistical data of the temperatures ...
    ref, med, pstd, mstd, pppstd, mmmstd = get_refstdev(outdoor, smoothened_temps)
    # ... and save them in an array p2
    p2 = [ref, med, pstd, mstd, pppstd, mmmstd]

    # And afterall ... plot them
    gu_comfort(p1)
    gu_scatterdata(p2, outdoor_s, smoothened_temps)

def get_stdev(time, temps):
    """
    get_stdev(time, temps)
    
    Get the standard deviations sigma and 3*sigma from a np.array
    - time = reference np.array of the timeline of the provided data
    - temps = np.array of data from which the standard deviation has to be known
    The function returns
    - median, p_stdev, m_stdev, ppp_stdev, mmm_stdev
    """

    try: 
        if len(time) == np.shape(temps)[0]:
            print 'stdev will be calculated'
        elif len(time) == np.shape(temps)[1]:
            temps = temps.T            
            print 'stdev will be calculated though after being transponed'
    except:
        raise IOError
    
    # basic definition of standard deviation figures
    one_std = int(np.shape(temps)[1] * 0.682689492137 / 2)
    three_std = int(np.shape(temps)[1] * 0.997300203937 / 2)
    print 'one_std is %s and three_std is %s' %(one_std, three_std)
    # sort all provided data in a new array with the same dimensions
    sorted_temps = np.zeros((np.shape(temps)[0],np.shape(temps)[1]))    
    for line in range(np.shape(temps)[0]):
        sorted_line = np.sort(temps[line, :])
        sorted_temps[line,:] = sorted_line
    # get the deviations of the provided data as five np.arrays
    median = sorted_temps[:, np.shape(temps)[1]/2]
    p_stdev = sorted_temps[:, np.shape(temps)[1]/2+one_std]
    m_stdev = sorted_temps[:, np.shape(temps)[1]/2-one_std]
    ppp_stdev = sorted_temps[:, np.shape(temps)[1]/2+three_std]
    mmm_stdev = sorted_temps[:, np.shape(temps)[1]/2-three_std]
    
    return median, p_stdev, m_stdev, ppp_stdev, mmm_stdev   

def gu_yeardata(time, ref, median, p_stdev, m_stdev, ppp_stdev, mmm_stdev):
    """
    gu_buitemp(time, outdoor, temps)
    
    plot a graphical unit of the indoor temperatures of #zones
    - time = reference np.array of the timeline of the provided data
    - outdoor = np.array of temperature
    - temps = np.array of data from which the plot is wanted
    """

    xticks = (0, 2678400, 5097600, 7776000, 10368000, 13046400, \
    15638400, 18316800, 20995200, 23587200, 26265600, 28857600, 31536000)
    xticknames =  ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', \
    'Aug', 'Sep', 'Oct', 'Nov', 'Dec', '')
    
    fig = plt.figure(1, figsize=(10, 4))
        # graphical unit for the large graph
    gu1 = AA.Subplot(fig, 1, 1, 1)
    fig.add_subplot(gu1)
    gu1.set_ylabel('Operative temperature, Celsius')
    gu1.set_ylim( (-10, 35) )
    gu1.set_yticks( (-10, -5, 0, 5, 10, 15, 20, 25, 30, 35) )
    # then we put the x-axes right
    # here it is possible to do _xmajortick and _xminortick
    gu1.axis['bottom', 'top', 'right'].set_visible(False)
    gu1.axis['timeline'] = gu1.new_floating_axis(nth_coord=0, \
    value=0, axis_direction = 'bottom')
    gu1.axis['timeline'].toggle(all=True)
    gu1.set_xlim( (0, 31536000) )
    gu1.set_xticks(xticks)
    gu1.set_xticklabels(xticknames, ha = 'left', size = 'small', rotation = 45)
    # gu_history.set_xminorticks[(-0, 2678400, 5097600, 7776000)]
    
    # then we put the title correct
    gu1.set_title('Temperature', ha = 'right', position = (0.17, 1))
    # then we plot the data
    p1 = gu1.plot(time, ref, color='red', lw = 1)
    p2 = gu1.plot(time, median, '--', color='black', lw = 1)
    p3 = gu1.plot(time, p_stdev, color='grey', lw = 1)
    p4 = gu1.plot(time, m_stdev, color='grey', lw = 1)
    gu1.plot(time, ppp_stdev, color='lightgrey', lw = 1)
    gu1.plot(time, mmm_stdev, color='lightgrey', lw = 1)
    # then we fill the plotted data
    gu1.fill_between(time, p_stdev, m_stdev, where = p_stdev >= m_stdev, \
    facecolor = 'grey', interpolate = True)    
    gu1.fill_between(time, ppp_stdev, p_stdev, where = ppp_stdev >= p_stdev, \
    facecolor = 'lightgrey', interpolate = True)    
    gu1.fill_between(time, m_stdev, mmm_stdev, where = m_stdev >= mmm_stdev, \
    facecolor = 'lightgrey', interpolate = True)  
    
    gu1.legend( (p1), ('Outdoor'), 'lower left')    
    gu1.legend( (p2), ('median'), 'lower center')    
    gu1.legend( (p3, p4), ('sigma','3*sigma'), 'lower right')    
    
    fig.show()
def get_refstdev(ref, temps):
    """
    get_stdev(time, temps)
    
    Get the standard deviations sigma and 3*sigma from a np.array
    - time = reference np.array of the timeline of the provided data
    - temps = np.array of data from which the standard deviation has to be known
    The function returns
    - median, p_stdev, m_stdev, ppp_stdev, mmm_stdev
    """

#    try: 
#        if len(time) == np.shape(temps)[0]:
#            print 'refstdev will be calculated'
#        elif len(time) == np.shape(temps)[1]:
#            temps = temps.T            
#            print 'stdev will be calculated though after being transponed'
#    except:
#        raise IOError
    print (len(ref))
    # get the order of sorting the reference temperature
    order = np.argsort(ref)
    # now sort the outdoor temperature from low to right and round-off to int
    ref = np.sort(ref)
    for i in range(len(ref)):
        ref[i] = int(ref[i])
    print len(ref)    
    # now we must order all indoor temperatures based on the same ref-ordering
    # first we make place for them and the nwe order them
    sorted_temps = np.zeros(np.shape(temps))
    for i in range(np.shape(temps)[0]):
        sorted_temps[i,:] = temps[order[i],:]
    # now we must determine all equal temperatures in ref and merge them
    merged_ref = []
    merged_ref = np.zeros(1)
    merged_ref[0] = ref[0]
    for i in range(1,len(ref)):
        if ref[i] != ref[i-1]:
            merged_ref = np.vstack((merged_ref,ref[i]))
    # now we know the amount of data and make place for them
    median = np.zeros(len(merged_ref))
    p_stdev = np.zeros(len(merged_ref))
    m_stdev = np.zeros(len(merged_ref))
    ppp_stdev = np.zeros(len(merged_ref))
    mmm_stdev = np.zeros(len(merged_ref))
    # now we must sort the indoor temperaturs to merged_ref
    for i in range(len(merged_ref)):
        ref_T = merged_ref[i]
        merged_temp = []
        for j in range(len(ref)):
            if ref[j] == ref_T:
                if len(merged_temp)==0: 
                    merged_temp = sorted_temps[j,:]
                else:
                    merged_temp = np.hstack((merged_temp,sorted_temps[j,:]))
        print '%s temps are found in merged_temp for Tref equal to %s' %(len(merged_temp), merged_ref[i])
        if len(merged_temp) != 0:
            a, b, c, d, e = get_singlestdev(merged_temp.T)
            median[i] = a
            p_stdev[i] = b
            m_stdev[i] = c
            ppp_stdev[i] = d
            mmm_stdev[i] = e

    print np.shape(merged_ref)
    print np.shape(median)
    print np.shape(p_stdev)
    print np.shape(m_stdev)
    print np.shape(ppp_stdev)
    print np.shape(mmm_stdev)

    return merged_ref, median, p_stdev, m_stdev, ppp_stdev, mmm_stdev   

def get_singlestdev(temps):
    """
    get_stdev(time, temps)
    
    Get the standard deviations sigma and 3*sigma from a np.array
    - time = reference np.array of the timeline of the provided data
    - temps = np.array of data from which the standard deviation has to be known
    The function returns
    - median, p_stdev, m_stdev, ppp_stdev, mmm_stdev
    """

    # basic definition of standard deviation figures
    one_std = int(len(temps) * 0.682689492137 / 2)
    three_std = int(len(temps) * 0.997300203937 / 2)
    print 'one_std is %s and three_std is %s' %(one_std, three_std)
    # sort all provided data in a new array with the same dimensions
    sorted_temps = np.sort(temps)
    # get the deviations of the provided data as five np.arrays
    median = sorted_temps[len(temps)/2]
    p_stdev = sorted_temps[len(temps)/2+one_std]
    m_stdev = sorted_temps[len(temps)/2-one_std]
    ppp_stdev = sorted_temps[len(temps)/2+three_std]
    mmm_stdev = sorted_temps[len(temps)/2-three_std]
    
    return median, p_stdev, m_stdev, ppp_stdev, mmm_stdev   


def gu_scatterdata(ref, median, p_stdev, m_stdev, ppp_stdev, mmm_stdev, outdoor, temps):
    """
    gu_buitemp(time, outdoor, temps)
    
    plot a graphical unit of the indoor temperatures of #zones
    - time = reference np.array of the timeline of the provided data
    - outdoor = np.array of temperature
    - temps = np.array of data from which the plot is wanted
    """

    fig = plt.figure(1, figsize=(4, 4))
        # graphical unit for the large graph
    gu1 = AA.Subplot(fig, 1, 1, 1)
    fig.add_subplot(gu1)
    gu1.set_ylabel('Operative temperature, Celsius')
    gu1.set_ylim( (-10, 35) )
    gu1.set_yticks( (-10, -5, 0, 5, 10, 15, 20, 25, 30, 35) )
    # then we put the x-axes right
    # here it is possible to do _xmajortick and _xminortick
    gu1.axis['bottom', 'top', 'right'].set_visible(False)
    gu1.axis['timeline'] = gu1.new_floating_axis(nth_coord=0, \
    value=0, axis_direction = 'bottom')
    gu1.axis['timeline'].toggle(all=True)
    gu1.set_xlim( (-10, 35) )
    gu1.set_xticks( (-10, -5, 0, 5, 10, 15, 20, 25, 30, 35) )
    
    # then we put the title correct
#    gu1.set_title('Temperature', ha = 'right', position = (0.17, 1))
    # then we plot the data
    gu1.plot(ref, ref, color='red', lw = 1)
    # scatterplot
    for i in range(np.shape(temps)[1]):
        gu1.scatter(outdoor,temps[:,i], marker='o', color='lightgrey',s=2,zorder=1) 
    # deviations
    gu1.plot(ref, median, '--', color='black', lw = 3,zorder=6)
    gu1.plot(ref, p_stdev, color='grey', lw = 2,zorder=5)
    gu1.plot(ref, m_stdev, color='grey', lw = 2,zorder=4)
    gu1.plot(ref, ppp_stdev, color='lightgrey', lw = 1,zorder=3)
    gu1.plot(ref, mmm_stdev, color='lightgrey', lw = 1,zorder=2)
# then we fill the plotted data
#    gu1.fill_between(ref, p_stdev, m_stdev, where = p_stdev >= m_stdev, \
#    facecolor = 'grey', interpolate = True)    
#    gu1.fill_between(ref, ppp_stdev, p_stdev, where = ppp_stdev >= p_stdev, \
#    facecolor = 'lightgrey', interpolate = True)    
#    gu1.fill_between(ref, m_stdev, mmm_stdev, where = m_stdev >= mmm_stdev, \
#    facecolor = 'lightgrey', interpolate = True)  
#    
#    gu1.legend( (p1), ('Outdoor'), 'lower left')    
#    gu1.legend( (p2), ('median'), 'lower center')    
#    gu1.legend( (p3, p4), ('sigma','3*sigma'), 'lower right')    
    
    fig.show()
