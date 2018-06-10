from bs4 import BeautifulSoup

# Doing this with BeatufilSoup is ugly. The webpy templator is much better!
# Will update later.

class Stock(object):
    """
        Defines the basic attributes to render for a stock
    """
    def __init__(self,name,symbol,sector,industry):
        self.name = name
        self.symbol = symbol
        self.sector = sector
        self.industry = industry 
        
        
    def render(self,soup):
        """
            Print HTML for the attributes of a stock
        """
        formTag = soup.new_tag('form')
        formTag['method'] = 'post'
        formTag['class'] = 'input'
        inputTag = soup.new_tag('input')
        inputTag['name'] = self.symbol
        inputTag['type'] = 'submit'
        inputTag['value'] = self.symbol
        stock_info = self.name + '\r\n' + 'Sector: ' + self.sector + '\r\n' + \
                     'Industry: ' + self.industry
        inputTag['title'] = stock_info
        formTag.append(inputTag)
        soup.body.append(formTag)
        return soup.prettify("utf-8")
        
        
    def plot_vol_return(self,f1,f2,date):
        """
            Render images of volumes and returns
        """
        soup = BeautifulSoup('',"html5lib")
        divTag = soup.new_tag('div')
        # Image tag for f1
        imgTag1 = soup.new_tag('img')
        imgTag1['src'] = f1
        imgTag1['alt'] = "Plot1"
        imgTag1['height'] = "500"
        imgTag1['width'] = "600"
        imgTag1['align'] = "left"
        # Image tag for f2
        imgTag2 = soup.new_tag('img')
        imgTag2['src'] = f2
        imgTag2['alt'] = "Plot2"
        imgTag2['height'] = "500"
        imgTag2['width'] = "600"
        # Append images for div tag
        divTag.append(imgTag1)
        divTag.append(imgTag2)
        soup.body.append(divTag)
        formTag = soup.new_tag('form')
        formTag['method'] = 'get'
        inputTag = soup.new_tag('input')
        inputTag['type'] = 'submit'
        inputTag['value'] = 'Back to Index'
        formTag.append(inputTag)
        divTag2 = soup.new_tag('div')
        divTag2['align'] = 'center'
        divTag2.append(formTag)
        # Add button to choose other dates
        formTag2 = soup.new_tag('form')
        formTag2['method'] = 'post'
        inputTag2 = soup.new_tag('input')
        inputTag2['type'] = 'text'
        inputTag2['name'] = date
        inputTag2['value'] = f1.split('/')[-1][:-4] +': ' + date
        inputTag2['size'] = 12
        formTag2.append(inputTag2)
        divTag3 = soup.new_tag('div')
        divTag3['align'] = 'center'
        divTag3.append(formTag2)
        #soup.body.append(formTag2)
        soup.body.append(divTag3)
        soup.body.append(divTag2)
        return soup.prettify("utf-8")


class StockIndex(object):
    def __init__(self,idx_name,nstocks,names,symbols,sectors,industries):
        self.idx_name = idx_name 
        self.nstocks = nstocks
        self.names = names
        self.symbols = symbols
        self.sectors = sectors
        self.industries = industries
        
        
    def group_in_table(self,soup):
        """
            Group symbols in html table
        """
        tabTag = soup.new_tag('table')
        captionTag = soup.new_tag('caption')
        hTag = soup.new_tag('h1')
        hTag.string = 'Nasdaq 100 Index'
        captionTag.append(hTag)
        tabTag.append(captionTag)
        nrows = round(self.nstocks/10)
        for row in range(nrows):
            trTag = soup.new_tag('tr')
            for colum in range(10):
                ind = 10*row + colum
                stock = Stock(self.names[ind],
                              self.symbols[ind],
                              self.sectors[ind],
                              self.industries[ind]
                              )
                emptySoup = BeautifulSoup('',"html5lib")             
                stockForm = BeautifulSoup(stock.render(emptySoup),"html5lib").form              
                tdTag = soup.new_tag('td')
                tdTag.append(stockForm)
                trTag.append(tdTag)
                tabTag.append(trTag)
        divTag = soup.new_tag('div')
        divTag['align'] = 'center'
        divTag.append(tabTag)
        soup.body.append(divTag)        
        #soup.body.append(tabTag)        
        formTag = soup.new_tag('form')
        formTag['method'] = 'post'
        inputTag = soup.new_tag('input')
        inputTag['type'] = 'submit'
        inputTag['name'] = 'Heatmap'
        inputTag['value'] = 'VolSpread Heatmap'
        formTag.append(inputTag)
        divTag2 = soup.new_tag('div')
        divTag2['align'] = 'center'
        brTag = soup.new_tag('br')
        divTag2.append(brTag)
        divTag2.append(formTag)
        soup.body.append(divTag2)
        return soup.prettify("utf-8")
        
    def plot_volspread_heatmap(self,f1,date):
        """
            Render images of volumes and returns
        """
        soup = BeautifulSoup('',"html5lib")
        divTag = soup.new_tag('div')
        divTag['align'] = 'center'
        # Image tag for f1
        imgTag = soup.new_tag('img')
        imgTag['src'] = f1
        imgTag['alt'] = "Plot Heatmap"
        imgTag['height'] = "570"
        imgTag['width'] = "900"
        # Append images for div tag
        divTag.append(imgTag)
        soup.body.append(divTag)  
        # Add button to choose other dates
        formTag2 = soup.new_tag('form')
        formTag2['method'] = 'post'
        inputTag2 = soup.new_tag('input')
        inputTag2['type'] = 'text'
        inputTag2['name'] = date
        inputTag2['value'] = date
        inputTag2['size'] = 6
        formTag2.append(inputTag2)
        divTag3 = soup.new_tag('div')
        divTag3['align'] = 'center'
        divTag3.append(formTag2)
        soup.body.append(divTag3)
        formTag = soup.new_tag('form')
        formTag['method'] = 'get'
        inputTag = soup.new_tag('input')
        inputTag['type'] = 'submit'
        inputTag['value'] = 'Back to Index'
        formTag.append(inputTag)
        divTag2 = soup.new_tag('div')
        divTag2['align'] = 'center'
        divTag2.append(formTag)
        
        soup.body.append(divTag2)
        return soup.prettify("utf-8")
        

# sp = BeautifulSoup('',"html5lib")
# spt = sp.new_tag('span')
# p1 = sp.new_tag('p')
# p1.string = 'par1'
# p2 = sp.new_tag('p')
# p2.string = 'par2'
# spt.append(p1)
# spt.append(p2)
# sp.append(spt)
# html = sp.prettify("utf-8")
# with open("templates/output.html", "wb") as file:
#     file.write(html)

# names = ['Apple Inc.', 'Facebook']
# symbols = ['AAPL','FB']
# sectors = ['Tech','Tech']
# industries = ['Computer Manufacturing','Internet Services']
# nasdaq = StockIndex('nasdaq100',2,names,symbols,sectors,industries)
# html = nasdaq.group_in_tables(soup)
#print(html)
# with open("templates/output.html", "wb") as file:
#       file.write(html.encode())
