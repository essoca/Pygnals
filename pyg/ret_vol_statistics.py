import pandas as pd
import numpy as np
from vol_processor import interpolate_return_volspread
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from os import mkdir, getcwd
from os.path import exists, join

data_dir = join(getcwd(),'data/')
img_dir = join(getcwd(),'images/')
    
def fit_return_volspread(stock_index,ticker,date,plot_result,**kwargs):
    """
        Fit returns in terms of the vol_spread signal
    """
    df, mov_avg_window, exc_delay_t, tstamps = interpolate_return_volspread(stock_index,\
                                                 ticker,date)            
    regressors = [
                 'Const',
                 'Vol_spread',
                 'Vol_spread_t-tau',
                 'Dummy_bot'
                 ]
    X = pd.DataFrame(columns=regressors)      
    # Estimate decay time of initial return
    tau_decay_ret0 = mov_avg_window/4
    X['Vol_spread'] = df['Vol_spread']* (df['Time'] > tau_decay_ret0).astype(float)  
    #X['Vol_spread_t-tau0'] = X['Vol_spread'].shift(int(tau_decay_ret0)).fillna(0)                   
    X['Vol_spread_t-tau'] = X['Vol_spread'].shift(mov_avg_window).fillna(0) 
    # Data belong to beginning of trading?
    X['Dummy_bot'] = df['Return'].ix[0]* np.exp(-df['Time']/tau_decay_ret0)*\
                     (df['Time'] < tau_decay_ret0).astype(float)
    X['Const'] = sm.add_constant(X)                         
    # Dummies to distinguish vol_spread drastic jumps
    abs_dvol_spread = abs(df['Vol_spread'].diff().fillna(0)) 
    q = abs_dvol_spread.quantile(0.995)                        
    id_jumps = np.array([0] + abs_dvol_spread[abs_dvol_spread > q].index.tolist())
    # If there are consecutive indexes in id_jumps, keep only first and last
    # This is convenient, e.g., to catch the end of trading effect
    consc = np.split(id_jumps, np.where(np.diff(id_jumps) != 1)[0]+1)
    new_ids = [x.tolist() if len(x) <= 2 else [x[0],x[-1]] for x in consc]
    first_consc = [x[0] for x in new_ids if len(x) > 2]
    # flatten new_ids
    id_jumps = [0]+[item for sublist in new_ids for item in sublist]
 
    for i in range(len(id_jumps)-1):
        df_dummies = pd.DataFrame(df.shape[0]*[0])
        df_dummies.loc[id_jumps[i]:id_jumps[i+1]] = 1        
        time_jump = df['Time'].loc[id_jumps[i+1]]        
        if time_jump in exc_delay_t:                
            # If the time of jump coincides with an excess request delay, identify
            # this type of dummy 
            regressors += ['Dummy_t'+ str(int(time_jump))+'_req_delay']
        elif id_jumps[i+1] in first_consc:
            regressors += ['Dummy_t'+ str(int(time_jump))+'+2consc']
        else:
            regressors += ['Dummy_t'+ str(int(time_jump))]
        X = pd.concat([X,df_dummies],axis=1)    
        
    X.columns = regressors    
    # Fit Return to vol_spread and dummies    
    ols = sm.OLS(df['Return'],X.astype(float)).fit() 
    
    if plot_result:
        dir_save = img_dir +'ret_vs_vol/'+ date +'/'
        if not exists(dir_save):
            mkdir(dir_save)
        if kwargs['tformat'] == 'tstamps':
            df['Time'] = tstamps['Time']    
        ax = df.plot(x='Time',y='Return',style='k',\
                    title='Intraday Returns for '+ ticker,legend=False)
        #df.plot(ax=ax,x='Time',y='Vol_spread',style='g',legend=False)
        zero = pd.DataFrame({'Time':df['Time'].values,'Return 0':np.zeros(df.shape[0])})
        zero.plot(ax=ax,x='Time',y='Return 0',style='--k',legend=False)
        ax.plot(df['Time'],ols.fittedvalues,'c',label='OLS')
        fig = ax.get_figure() 
        fig.set_size_inches(8, 6)
        fig.savefig(dir_save+ticker+'.png',bbox_inches='tight',dpi=100)
        plt.close(fig)
    else:
        return ols, X['Vol_spread'].mean(), X['Vol_spread'].std(),\
        df['Return'].loc[int(tau_decay_ret0):].sum(),\
        np.sum(ols.fittedvalues[int(tau_decay_ret0)])           


def plot_return_vs_volspread(stock_index,date):
    """
        Plot returns and volume spread together with the fitted values of
        return explained by the volume spread
    """
    tickers = pd.read_csv(data_dir+ stock_index+ '/'+ stock_index+'_atoms.csv',\
                            usecols=['Ticker'])
    tickers = tickers['Ticker'].values.tolist()       
    for ticker in tickers:
        try:
            print('Ploting return vs volSpread for {}'.format(ticker))
            fit_return_volspread(stock_index,ticker,date,True,tformat='tstamps')
        except (KeyError,IOError):
            continue
    
def return_volspread_stat(stock_index,date):
    """Calculate requested statistics on the stock index"""
    
    cols = [
            'Ticker',
            'P_const > |t|',
            'P_vol_spread > |t|',
            'P_vol_spread_t-tau > |t|',
            'P_bot > |t|',
            '# extra params',
            'Traded as | Vol_spread (avg,std)',
            'Total avg ret (t>tau0)',
            'Total avg ret (pred)',
            'R^2'
           ]           
    df_stat = pd.DataFrame(columns=cols)
    df_stat.to_csv(data_dir+stock_index+'/'+date+'/stat_'+date+'.csv')
    tickers = pd.read_csv(data_dir+ stock_index +'_atoms.csv',usecols=['Ticker'])
    tickers = tickers['Ticker'].values.tolist()
    
    for k, ticker in enumerate(tickers):    
    # Some symbols in stock_index_atoms are not in the old fundm_date files     
        try:
            print('Fitting Return vs Vol_spread for {}'.format(ticker))
            ols, avg_vs, std_vs, tot_avg_ret, tot_pred_avg_ret = \
                            fit_return_volspread(stock_index,ticker,date,False)
                
            join_pair = lambda x,y: str(round(x,2)) + ', ' + str(round(y,2))
            neutral = 0.05
            moderate = 0.3
            if abs(avg_vs) <= neutral:
                signal = 'neutral | ' + join_pair(avg_vs,std_vs)
            elif neutral < avg_vs <= moderate:
                signal = 'buy | ' + join_pair(avg_vs,std_vs)
            elif avg_vs > moderate:
                signal = 'strong buy | ' + join_pair(avg_vs,std_vs)
            elif -neutral > avg_vs >= -moderate:
                signal = 'sell | ' + join_pair(avg_vs,std_vs)
            else:
                signal = 'strong sell | ' + join_pair(avg_vs,std_vs)
        
            row = [
                    ticker,
                    ols.pvalues[0],
                    ols.pvalues[1],
                    ols.pvalues[2],
                    ols.pvalues[3],
                    len(ols.params)-3,
                    signal,
                    tot_avg_ret,
                    tot_pred_avg_ret,
                    ols.rsquared
                  ]                      
            pd.DataFrame([[k]+row]).round(3).set_index(0).\
            to_csv(data_dir+stock_index+'/'+date+'/stat_'+date+'.csv',mode='a',\
                   header=False)    
        except(KeyError,IOError):
            continue                         