import web
from web import form
import os
from os.path import join
from os import getcwd
from bs4 import BeautifulSoup
import pandas as pd

#=============================================================================
pyg_dir = join(getcwd(),'pyg/')

def load_imports(path):
    """
        Import all modules from pyg_main
    """
    files = os.listdir(path)
    imps = []

    for i in range(len(files)):
        name = files[i].split('.')
        if len(name) > 1:
            if name[1] == 'py' and name[0] != '__init__':
               name = name[0]
               imps.append(name)
               
    file = open(path+'__init__.py','w')
    toWrite = '__all__ = ' + str(imps)
    file.write(toWrite)
    file.close()

load_imports(pyg_dir)    
from pyg import pyg_web as pw
from pyg import stock_fundamentals as sf
#=============================================================================

templates_dir = join(getcwd(),'templates/')
data_dir = join(getcwd(),'data/')
stock_index = 'nasdaq100'

stocks = pd.read_csv(data_dir+ stock_index+ '/'+ stock_index+'_atoms.csv')
symbols = stocks['Ticker'].values.tolist()   
names = stocks['Name'].values.tolist()   
sectors = stocks['Sector'].values.tolist()  
industries = stocks['Industry'].values.tolist()   
nstocks = len(names)

class index: 
    
    def GET(self): 
        with open(templates_dir+'layout.html') as fp:
             soup = BeautifulSoup(fp,"html5lib")
        nasdaq = pw.StockIndex(stock_index,nstocks,names,symbols,sectors,industries)
        return nasdaq.group_in_table(soup)
    
    
    def POST(self): 
        inputdata = web.input()
        data = list(inputdata.values())[0]
        date = sf.todays_date_mmddyy()
        # date = '062917'
        nasdaq = pw.StockIndex('nasdaq100',2,names,symbols,sectors,industries)
        if data == 'VolSpread Heatmap' or len(list(data)) == 6:
            if len(list(data)) == 6:
                date = data
            f1 = '/images/vol_heatmaps/'+ date + '.png'
            return nasdaq.plot_volspread_heatmap(f1,date)
        else:
            if len(list(data)) < 6:
                symbol = data
            elif len(list(data)) > 6:
                symbol_date = data.split(':') 
                symbol = symbol_date[0]
                date = symbol_date[1][1:]
            try:
                f1 = '/images/vol_evolution/'+ date +'/'+ symbol + '.png'
                f2 = '/images/ret_vs_vol/'+ date +'/'+ symbol + '.png'
                idSymbol = symbol == symbols
                name = names[idSymbol]
                sector = sectors[idSymbol]
                industry = industries[idSymbol]
                stock = pw.Stock(name,symbol,sector,industry)
                return stock.plot_vol_return(f1,f2,date)
            except:
                with open(templates_dir+'layout.html') as fp:
                    soup = BeautifulSoup(fp,"html5lib")
                return nasdaq.group_in_table(soup)

class ImageDisplay(object):
    
    def GET(self,name):
        ext = name.split(".")[-1] # get extension
        cType = {
                 'png': "/images/png",
                 'svg': "/images/svg"
                 }
        def list_dirs(root_dir):
            """ List files in root_dir AND its subdirectories"""
            fls = []
            for path, subdirs, files in os.walk(root_dir):
                for name in files:
                     fls += [os.path.join(path, name)]
            return fls  
        # Open image if found 
        if 'images/{}'.format(name) in list_dirs('images'):
            web.header("Content-Type", cType[ext])
            return open('images/{}'.format(name),"rb").read()
        else:
            raise web.notfound()  

urls = ('/', 'index',
        '/images/(.*)', 'ImageDisplay'
        )
        
#render = web.template.render('templates/',base="layout")        
app = web.application(urls, globals())

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()