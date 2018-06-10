import pandas as pd
import numpy as np
from os import mkdir, getcwd
from os.path import exists, join
import stock_fundamentals as sf 
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

data_dir = join(getcwd(),'data/')
img_dir = join(getcwd(),'images/')

def split_buy_sell_vols(stock_index,ticker,date):
    """
        Build buy/sell volume signals and stock returns.
        Buy/Sell volumes are divided into the following categories:
        -----------------------------------------------------------
        Strong Buy: 3, 
        Buy: 2, 
        Mid Spread Buy: 1,
        Mid Spread Sell: -1,
        Sell: -2, 
        Strong Sell: -3.         
    """
    input_dir = data_dir + stock_index + '/' + date + '/'
    df = pd.read_csv(input_dir + 'order_book/' + ticker +'.csv')
    # Volume of signal         
    vol_signal = pd.DataFrame(columns=['Time','Signal','Vol'])
    vol_buy = 0
    vol_sell = 0     
    for k in range(df.shape[0]):        
        bid, ask = df['Bid'][k], df['Ask'][k]
        last_price = df['Last Price'][k]
        last_size = df['Last Size'][k]
        t = df['Unnamed: 0'][k]
        if last_price == bid:
            # At the bid
            vol_sell += last_size 
            vol_signal.loc[vol_signal.shape[0]] = [t,-3,vol_sell]
        elif last_price == ask:
            # At the ask
            vol_buy += last_size
            vol_signal.loc[vol_signal.shape[0]] = [t,3,vol_buy]
        elif abs(last_price-bid) < abs(last_price-ask):
            # Near the bid
            vol_sell += last_size
            vol_signal.loc[vol_signal.shape[0]] = [t,-2,vol_sell]
        elif abs(last_price-bid) > abs(last_price-ask):
            # Near the ask
            vol_buy += last_size
            vol_signal.loc[vol_signal.shape[0]] = [t,2,vol_buy]
        else:
            # When at the middle of bid-ask spread or (no ask | no bid)
            # Randomly assign a buy (1) or sell (0) signal
            if np.random.randint(2) == 1:
                vol_buy += last_size
                vol_signal.loc[vol_signal.shape[0]] = [t,1,vol_buy]
            else:
                vol_sell += last_size
                vol_signal.loc[vol_signal.shape[0]] = [t,-1,vol_sell]      
    # Normalize volumes with respect to float shares
    fundm = input_dir + 'fundm_' + date + '.csv'
    if not exists(fundm):
        #sf.request_fundamentals(stock_index)
        sf.yahoof_key_statistics(stock_index)
    # Float from billions to millions    
    Float = 1e9*pd.read_csv(fundm,index_col='Ticker').loc[ticker]['Float']
    #Float = pd.read_csv(fundm,index_col='Ticker').loc[ticker]['Float']
    # Express results in basis points (*10^4)           
    bp = 1e4     
    vol_signal['Vol'] = bp * vol_signal['Vol']/Float       
    # Time stamps of trading events
    tstamps = pd.concat([df['Unnamed: 0'],pd.to_datetime(df['Time']).dt.time],axis=1)
    return vol_signal, tstamps                                      


def get_buy_sell_vols(stock_index,ticker,date):
    """
        Calculate intraday buy/sell volumes and stock returns.
        Does not divide volumes into further categories.
    """
    input_dir = data_dir + stock_index + '/' + date + '/'
    df = pd.read_csv(input_dir + 'order_book/' + ticker +'.csv')
    # Buy/sells are transactions occuring near/at the ask/bid prices
    vol_b = pd.DataFrame(columns=['Time','Vol_b'])
    vol_s = pd.DataFrame(columns=['Time','Vol_s'])
    # Returns 
    ret = pd.DataFrame(columns=['Time','Return'])   
    vol_buy = 0
    vol_sell = 0
    dt = 5        
    exc_delay_t = []    
    for k in range(df.shape[0]):        
        bid, ask = df['Bid'][k], df['Ask'][k]
        last_price = df['Last Price'][k]
        last_size = df['Last Size'][k]        
        req_delay = df['Request Delay'][k]
        t = df['Unnamed: 0'][k]
        ret.loc[ret.shape[0]] = [t,last_price]         
        if abs(last_price-bid) < abs(last_price-ask):
            # Near/at the bid
            vol_sell += last_size
            vol_s.loc[vol_s.shape[0]] = [t,vol_sell]            
        elif abs(last_price-bid) > abs(last_price-ask):
            # Near the ask
            vol_buy += last_size
            vol_b.loc[vol_b.shape[0]] = [t,vol_buy]            
        else:
            # When at the middle of bid-ask spread or (no ask | no bid)
            # Randomly assign a buy (1) or sell (0) signal
            if np.random.randint(2) == 1:
                vol_buy += last_size
                vol_b.loc[vol_b.shape[0]] = [t,vol_buy]
            else:
                vol_sell += last_size
                vol_s.loc[vol_s.shape[0]] = [t,vol_sell]
        #Record if there was excess request delay at this time
        if req_delay > dt: exc_delay_t += [t]                
    # Normalize volumes with respect to float shares
    fundm = input_dir + 'fundm_' + date + '.csv'
    if not exists(fundm):
        #sf.request_fundamentals(stock_index)
        sf.yahoof_key_statistics(stock_index)
    # Float from billions to millions    
    Float = 1e9*pd.read_csv(fundm,index_col='Ticker').loc[ticker]['Float']
    #Float = pd.read_csv(fundm,index_col='Ticker').loc[ticker]['Float']
    # Express results in basis points (*10^4)           
    bp = 1e4            
    vol_b['Vol_b'] = bp * vol_b['Vol_b']/Float
    vol_s['Vol_s'] = bp * vol_s['Vol_s']/Float

    ret['Return'] = bp *ret['Return'].diff()/ret['Return']  
    ret['Return'] = ret['Return'].shift(-1).fillna(ret['Return'].iloc[-1]) 
    # Time stamps of trading events
    tstamps = pd.concat([df['Unnamed: 0'],pd.to_datetime(df['Time']).dt.time],axis=1)  
    return vol_b, vol_s, ret, exc_delay_t, tstamps 
       
        
def moving_avg(df,column,window):
    """
        Calculate moving average of given column in df.
        For the first data within window, build avg as a random walk. This 
        introduces an effect that must be accounted for when fitting.
    """
    nrow = df.shape[0]
    if window > nrow:
        window = int(0.25*nrow)
    mov_avg = nrow*[0] 
    roll_sum = 0
    for j in range(window):
        roll_sum = sum(df[column].iloc[:j+1])
        mov_avg[j] = roll_sum/(j+1)
    for k in range(nrow-window):
        roll_sum += df[column].iloc[window+k]-df[column].iloc[k]
        mov_avg[window+k] = roll_sum/window
    df[column] = mov_avg
    return df    

   
def merge_vols(df1,df2,buy_or_sell):
    """
        Merge volumes keeping the correct order of respective times
    """
    if df1.empty:
        return df2
    if df2.empty:
        return df1        
    times1 = np.append(np.array(df1['Time']),float('Inf'))
    times2 = np.append(np.array(df2['Time']),float('Inf'))
    out_size = df1.shape[0] + df2.shape[0]    
    Vol_out = 'Vol_' + buy_or_sell
    df = pd.DataFrame(columns=['Time',Vol_out])
    i, j = 0, 0
    for k in range(out_size):
        if times1[i] < times2[j]:
            df.loc[df.shape[0]] = [ df1.iloc[i,0], df1.iloc[i,1] ]
            i += 1
        else:
            df.loc[df.shape[0]] = [ df2.iloc[j,0], df2.iloc[j,1] ]
            j += 1
    return df    
 
 
def vol_interpolate(df1,df2,buy_sell):
    """
        Interpolate df1 at the time values of df2
    """
    if df2.empty:
        return df1
    sz2 = df2.shape[0]
    dft2 = pd.concat([df2['Time'],pd.DataFrame(sz2*[float('Nan')])],axis=1)
    return merge_vols(df1,dft2,buy_sell).interpolate()                                
    
    
def plot_interpolate_volspread(stock_index,ticker,date,**kwargs):    
    """Merge all buy volumes, all sell volumes and interpolate results in order
       to be able to define the buy/sell volume spread. 
       Returns are moving-averaged.
    """
    vol_signal, tstamps = split_buy_sell_vols(stock_index,ticker,date)
    vol_sbuy = pd.DataFrame(columns=['Time','Vol Strong Buy'])
    vol_wbuy = pd.DataFrame(columns = ['Time','Vol Buy'])
    vol_mspbuy = pd.DataFrame(columns = ['Time','Vol Mid Spread Buy'])
    vol_mspsell = pd.DataFrame(columns = ['Time','Vol Mid Spread Sell'])
    vol_wsell = pd.DataFrame(columns = ['Time','Vol Sell'])
    vol_ssell = pd.DataFrame(columns = ['Time','Vol Strong Sell'])
    
    a = vol_signal.loc[vol_signal['Signal']==3][['Time','Vol']]
    vol_sbuy = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Strong Buy': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal']==2][['Time','Vol']]                        
    vol_wbuy = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Weak Buy': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal']==1][['Time','Vol']]                           
    vol_mspbuy = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Mid Spread Buy': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal']==-1][['Time','Vol']]                             
    vol_mspsell = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Mid Spread Sell': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal']==-2][['Time','Vol']]                            
    vol_wsell = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Weak Sell': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal']==-3][['Time','Vol']]                            
    vol_ssell = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Strong Sell': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal'].isin([3,2,1])][['Time','Vol']]
    vol_buy = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Buy': a['Vol'].values})
    a = vol_signal.loc[vol_signal['Signal'].isin([-3,-2,-1])][['Time','Vol']]
    vol_sell = pd.DataFrame({'Time': a['Time'].values, \
                            'Vol Sell': a['Vol'].values})
    # Interpolate buy and sell volumes to have trading events at common times
    vol_buy_interp = vol_interpolate(vol_buy,vol_sell,'buy').fillna(0)
    vol_sell_interp = vol_interpolate(vol_sell,vol_buy,'sell').fillna(0)
    # Volume spread
    Vol_spread = vol_buy_interp['Vol_buy'] - vol_sell_interp['Vol_sell']    
    vol_buy_interp['Vol_spread'] = Vol_spread 
    # Set the format for Time: tseries (default) or timestamps  
    intt2stamp = lambda df, ts: pd.Series(ts.loc[ts['Unnamed: 0'].isin(df['Time'].\
                                astype(int))]['Time'].values)
    if kwargs['tformat'] == 'tstamps':
        vol_buy_interp['Time'] = tstamps['Time']
        vol_sell_interp['Time'] = tstamps['Time']
        vol_wbuy['Time'] = intt2stamp(vol_wbuy,tstamps)
        vol_wsell['Time'] = intt2stamp(vol_wsell,tstamps)
        vol_sbuy['Time'] = intt2stamp(vol_sbuy,tstamps)
        vol_ssell['Time'] = intt2stamp(vol_ssell,tstamps)        
        vol_mspbuy['Time'] = intt2stamp(vol_mspbuy,tstamps)
        vol_mspsell['Time'] = intt2stamp(vol_mspsell,tstamps)

    ax=vol_wbuy.plot(x='Time',y='Vol Weak Buy',marker='o',linestyle='dashed',\
            color=(0.4,0.7,1),title='Buy and Sell Volumes for '+ ticker,legend=False)
    vol_wsell.plot(ax=ax,x='Time',y='Vol Weak Sell',marker='o',\
            linestyle='dashed',color=(1,0.6,0.6),legend=False)    
    if not vol_sbuy.empty:
        vol_sbuy.plot(ax=ax,x='Time',y='Vol Strong Buy',style='ob',legend=False)
    if not vol_ssell.empty:    
        vol_ssell.plot(ax=ax,x='Time',y='Vol Strong Sell',style='or',legend=False)
    if not vol_mspbuy.empty:
        vol_mspbuy.plot(ax=ax,x='Time',y='Vol Mid Spread Buy',style='og',legend=False)  
    if not vol_mspsell.empty:
        vol_mspsell.plot(ax=ax,x='Time',y='Vol Mid Spread Sell',style='og',legend=False)  
                                        
    dir_save = img_dir +'vol_evolution/'+ date +'/'
    if not exists(dir_save):
        mkdir(dir_save)
    fig = ax.get_figure() 
    fig.set_size_inches(8, 6)
    fig.savefig(dir_save+ticker+'.png',bbox_inches='tight',dpi=100)
    plt.close(fig)


def interpolate_return_volspread(stock_index,ticker,date):    
    """ Interpolate buy/sell volumes in order to be able to define the 
        buy/sell volume spread. Returns are moving-averaged.
    """
    vol_b, vol_s, ret, exc_delay_t, tstamps = get_buy_sell_vols(stock_index,ticker,date)
    #Determine size of moving average window
    mov_avg_window = int(ret.shape[0]/5.)                
    # Moving average of returns        
    avg_ret = moving_avg(ret,'Return',mov_avg_window)         
    # Interpolate buy and sell volumes to have trading events at common times
    vol_buy_interp = vol_interpolate(vol_b,vol_s,'buy').fillna(0)
    vol_sell_interp = vol_interpolate(vol_s,vol_b,'sell').fillna(0)
    # Volume spread
    Vol_spread = vol_buy_interp['Vol_buy'] - vol_sell_interp['Vol_sell']
    Vol_spread = pd.DataFrame({'Vol_spread': Vol_spread})
    return pd.concat([avg_ret['Time'],avg_ret['Return'],Vol_spread],axis=1),\
           mov_avg_window, exc_delay_t, tstamps               


def plot_intraday_vols(stock_index,date):
    """
        Plot the intraday evolution of the volume spread and the returns
    """
    tickers = pd.read_csv(data_dir+ stock_index +'/'+stock_index +'_atoms.csv',\
                          usecols=['Ticker'])
    tickers = tickers['Ticker'].values.tolist()
    for ticker in tickers:
        try:
            print('Ploting volume data for {}'.format(ticker))
            plot_interpolate_volspread(stock_index,ticker,date,tformat='tstamps')
        except (KeyError,IOError):
            continue

    
def buy_sell_heatmap(stock_index,date):
    """
        Plot heatmap of a given stock index on given date
    """
    tickers = pd.read_csv(data_dir+ stock_index +'/'+stock_index +'_atoms.csv',\
                          usecols=['Ticker'])
    tickers = tickers['Ticker'].values.tolist()
    avg_volSpread = []
    stocks_in_index = [] 
    for k, ticker in enumerate(tickers):
        try:
            print('Adding {} info to heatmap'.format(ticker))
            df, a, b, c = interpolate_return_volspread(stock_index,ticker,date)
            avg_volSpread += [df['Vol_spread'].mean()]
        except (KeyError,IOError):
            continue
        stocks_in_index += [k]

    tickers = [tickers[i] for i in stocks_in_index]
    df = pd.DataFrame({'Signal': avg_volSpread}, index= tickers)
    
    sectors = pd.read_csv(data_dir + stock_index +'/'+stock_index +'_atoms.csv',\
                          usecols=['Ticker','Sector','Industry'],\
                          index_col='Ticker')    
    df.insert(0,'Sector',sectors['Sector'])  
    df.insert(1,'Industry',sectors['Industry'])  
    sector_list = sectors['Sector'].drop_duplicates().values
    industry_list = sectors['Industry'].drop_duplicates().values
    # Group stocks in the index by sectors (ignore stocks with no sector info)
    bysector_df = pd.DataFrame()          
    for sec_name, group in df.groupby(['Sector','Industry']):
        bysector_df = pd.concat([bysector_df,group],axis=0)     
    
    sect_list_short = {
                        sector_list[0]: 'Tech: ',
                        sector_list[1]: 'Misc: ',
                        sector_list[2]: 'Health: ',
                        sector_list[3]: 'Serv: ',
                        sector_list[4]: 'Transp: ',
                        sector_list[5]: 'ConsND: ',
                        sector_list[6]: 'Goods: ',
                        sector_list[7]: 'Utils: '
                      }
    indt_list_short = {
                        industry_list[0]: 'Prepkg Sftw',
                        industry_list[1]: 'Busin Srv',
                        industry_list[2]: 'Pharmacy',
                        industry_list[3]: 'Intn Sftw',
                        industry_list[4]: 'Catg Dist',
                        industry_list[5]: 'AirDlv Srv',
                        industry_list[6]: 'Bio Prod',
                        industry_list[7]: 'Semicond',
                        industry_list[8]: 'Comp Manf',
                        industry_list[9]: 'EDP Srv',
                        industry_list[10]: 'TV Srv',
                        industry_list[11]: 'Apparel',
                        industry_list[12]: 'Comm Eqp',
                        industry_list[13]: 'Retl Str',
                        industry_list[14]: 'Railroads',
                        industry_list[15]: 'Med Inst',
                        industry_list[16]: 'Trsp Srv',
                        industry_list[17]: 'Med Srv',
                        industry_list[18]: 'Build Mtr',
                        industry_list[19]: 'Recrt Prod',
                        industry_list[20]: 'Med Spec',
                        industry_list[21]: 'Med Elect',
                        industry_list[22]: 'Bio Diagn',
                        industry_list[23]: 'Bio Lab Inst',
                        industry_list[24]: 'Bio Resch',
                        industry_list[25]: 'Idtry Spec',
                        industry_list[26]: 'Courier Srv',
                        industry_list[27]: 'Oth Spec Str',
                        industry_list[28]: 'Elect Comp',
                        industry_list[29]: 'Ind Mach Comp',
                        industry_list[30]: 'Hotel/Resort',
                        industry_list[31]: 'Packg Food',
                        industry_list[32]: 'Bvrg Prod',
                        industry_list[33]: 'ElecVid Chns',
                        industry_list[34]: 'Mar Transp',
                        industry_list[35]: 'Auto Manf',
                        industry_list[36]: 'Comerc Srv',
                        industry_list[37]: 'RTV broadc',
                        industry_list[38]: 'Cloth Str',
                        industry_list[39]: 'Broadcastg',
                        industry_list[40]: 'Restaurant',
                        industry_list[41]: 'Telecom Eqp'
                      }                  
    new_index = bysector_df.index + bysector_df['Sector'].apply(\
                lambda x: '   (' + sect_list_short[x]) + \
                                    bysector_df['Industry'].apply(\
                lambda x: indt_list_short[x] + ')')
      
    tk = pd.DataFrame({'Signal': bysector_df['Signal'].values},\
                       index = new_index.rename('Symbol')).astype(float)            
    # Plot heatmap
    import seaborn as sns  
    # rc = {'font.size': 32, 'axes.labelsize': 32, 'legend.fontsize': 32.0, 
    #       'axes.titlesize': 32, 'xtick.labelsize': 32, 'ytick.labelsize': 32}
    rc = {'axes.labelsize': 9, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
          'font.family': 'Arial'}
    sns.set(rc=rc)      
    max_s = tk.max().values[0]
    min_s = tk.min().values[0]
    fig, ax = plt.subplots(1,2)      
    sns.set(font_scale=0.7)
    sns.heatmap(tk.iloc[:50],cmap=plt.cm.bwr_r,ax=ax[0],vmax=max_s,vmin=min_s)
    sns.heatmap(tk.iloc[50:],cmap=plt.cm.bwr_r,ax=ax[1],vmax=max_s,vmin=min_s)
    # wspace increases distance between plots
    plt.subplots_adjust(left=0.15,bottom=0.09,right=0.95,top=0.92,\
                        wspace=1.5,hspace = 0.21)
    #plt.subplot_tool()
    #fig.show()
    fig.savefig(getcwd()+'/images/vol_heatmaps/'+date+'.png',bbox_inches='tight',\
                dpi=100)