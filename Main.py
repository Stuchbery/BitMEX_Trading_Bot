from time import sleep
from threading import Thread
from FILO_ORDERS import FILO_ORDERS
import BITMEX_API_CURL as BAC
import socket

class Bot:
    def loadStrategy(self,fn):
        f = open(fn, 'r')
        lines = f.readlines()
        for line in lines:
            if len(line) > 1:
                line = line.lstrip(' ')
                if '#' not in line[0]:
                    if 'OrderQtyPercentage' in line:
                        self.OrderQtyPercentage = float(str(line).split('::')[1].strip())
                    if 'Spread' in line:
                        self.spread = int(str(line).split('::')[1].strip())
                    if 'JSON_API_KEY' in line:
                        self.JSON_API_KEY = str(line).split('::')[1].strip()
                    if 'JSON_API_SECRET' in line:
                        self.JSON_API_SECRET = str(line).split('::')[1].strip()
                    if 'API_ENDPOINT' in line:
                        self.API_ENDPOINT = str(line).split('::')[1].strip()
                    if 'PROGRAM_NAME' in line:
                        self.PROGRAM_NAME = str(line).split('::')[1].strip()
                    if 'DELTA_SRV_HOST' in line:
                        self.DELTA_SRV_HOST = str(line).split('::')[1].strip()
                    if 'DELTA_SRV_PORT' in line:
                        self.DELTA_SRV_PORT = int(str(line).split('::')[1].strip())

        f.close()

    def __init__(self):
        ### Requirements ###
        # Note this Market Making Algorithm uses the Bitmex DeltaServer To retieve the current "Quote" Price of XBTUSD
        # https://github.com/BitMEX/api-connectors/tree/master/official-ws/delta-server
        # Once the DeltaServer is setup you can specify to host and port of the Delta Server in the fxcm.cfg
        #
        # We also log messages and send them to the MM_BITMEX_LOGGING_SERVER on port 7777 to running on  localhost
        # run MM_BITMEX_LOGGING_SERVER locally as a service
        # 'nohup python2.7 MM_BITMEX_LOGGING_SERVER.py &'
        #

        ### Values loaded from fxcm.cfg ###
        self.PROGRAM_NAME       = ''    # used in logging
        self.JSON_API_KEY       = ''
        self.JSON_API_SECRET    = ''
        self.OrderQtyPercentage = 2
        self.spread             = 51
        self.API_ENDPOINT       = ''
        self.DELTA_SRV_HOST     = ''
        self.DELTA_SRV_PORT     = ''
        self.loadStrategy('./settings.conf')
        #################

        self.BID_PRICE              = 0
        self.ASK_PRICE              = 0
        self.firstrun               = True
        self.currGapPrice           = 0
        self.currSellPrice          = 0
        self.currBuyPrice           = 0
        self.availMargin            = 0
        self.getMarginDelay         = 60*60     # seconds
        self.getQuotesDelay         = 0.5       # seconds
        self.logging_server_port    = 7777
        self.Control_Value          = 0          # denotes how many outstanding buys/sells are required to be filled
        #################

        self.bmx_curl               = BAC.BITMEX_API_CURL(self.DELTA_SRV_HOST,self.DELTA_SRV_PORT,self.logging_server_port,self.PROGRAM_NAME,self.API_ENDPOINT,self.JSON_API_KEY, self.JSON_API_SECRET,'XBTUSD')
        self.bmx_curl_Margin        = BAC.BITMEX_API_CURL(self.DELTA_SRV_HOST,self.DELTA_SRV_PORT,self.logging_server_port,self.PROGRAM_NAME,self.API_ENDPOINT,self.JSON_API_KEY, self.JSON_API_SECRET,'XBTUSD')


        thread_AM = Thread(target=self.getMarginMain) #Retrieve availMagin at reqular intervals
        thread_AM.daemon = True
        thread_AM.start()
        sleep(5)

        thread_QD = Thread(target=self.getQuotesMain)  #Retrieve current price of BTC/USD at reqular intervals
        thread_QD.daemon = True
        thread_QD.start()
        sleep(5)

        #Object for "First In Last Out" queue using txt files (good if you need to restart).
        #Helps keep track of how much we need to buy/sell back.
        self.filo = FILO_ORDERS(self.availMargin,self.OrderQtyPercentage)

        #Main Loop
        self.injectMarketOrdersMain()

    ### MARKET EVENT METHODS ###
    def MarketEventsLoopMain(self):
        while True:
            try:
                self.MarketEvents()
            except Exception as e:
                self.sendLogToServer('MarketEvents', 'Error', str(e.message))
                sleep(1)
    def MarketEvents(self):
        # This thread reacts to the changes in the market price.
        # if the price changes as much or more/less than the spread it increments/decrements the Control_Value

        if self.firstrun == True:
            self.currGapPrice = self.ASK_PRICE   #self.getCurrentOrderPricelvl(self.OrderPrices)
            self.currSellPrice = self.currGapPrice + self.spread
            self.currBuyPrice = self.currGapPrice - self.spread
            log = "Market events init: " + str(self.currGapPrice) + "-" + str(self.currSellPrice) + "-" + str(self.currBuyPrice) +'\n'+'TRADE FLAT '+'-'+str(self.Control_Value)+'-' + str(self.ASK_PRICE)+ '-' + str(self.OrderQtyPercentage) + '-' + str(self.availMargin)
            self.sendLogToServer('MarketEvents', 'Info', log)
            self.firstrun = False
        else:
            if self.BID_PRICE > self.currSellPrice:
                #send Sell Order
                self.Control_Value = self.Control_Value + 1
                log = "Sell Order: " + str(self.ASK_PRICE)+"-"+ str(self.currSellPrice)+"-"+ "self.Control_Value: " + str(self.Control_Value)
                self.sendLogToServer('MarketEvents', 'Info', log)
                #currGapPrice = currSellPrice
                self.currBuyPrice = self.currSellPrice - self.spread
                self.currSellPrice = self.currSellPrice + self.spread
            elif self.ASK_PRICE < self.currBuyPrice:
                #send Buy Order
                self.Control_Value = self.Control_Value - 1
                log = "Buy Order: " + str(self.ASK_PRICE) + "-" + str(self.currBuyPrice) + "-" + "self.Control_Value: " + str(self.Control_Value)
                self.sendLogToServer('MarketEvents', 'Info', log)
                #currGapPrice = currBuyPrice
                self.currSellPrice = self.currBuyPrice + self.spread
                self.currBuyPrice = self.currBuyPrice - self.spread

    ### InjectMarketOrders Thread ###
    def injectMarketOrdersMain(self):
        while True:
            try:
                self.injectMarketOrders()
            except Exception as e:
                self.sendLogToServer('injectMarketOrdersMain', 'Error', str(e.message))
                sleep(1)
    def injectMarketOrders(self):
        #Checks the Control_Value and sells or buys if value is high or low respectively.
        #Aims to keep Control_Value equal to 0

        if self.Control_Value > 0:
            OrderQty = self.filo.getOrderValueSell(self.ASK_PRICE)
            if OrderQty == 0:
                self.sendLogToServer('injectMarketOrders', 'Info_OrderQty', str(OrderQty))
                #print('injectMarketOrders_Info_OrderQty_Sell: ' + str(OrderQty))
            else:
                isSuccsessful, respSell = self.bmx_curl.setTrailingSellMarketOrder(OrderQty)
                if isSuccsessful == True and self.Control_Value > 0:
                    self.filo.isSuccessfulOrderValueSell(OrderQty)
                    self.Control_Value = self.Control_Value - 1
                    log = 'TRADE UP   '+'-'+str(self.Control_Value)+'-'  + str(self.ASK_PRICE) + '-' + str(OrderQty) + '-' + str(self.availMargin)
                    self.sendLogToServer('injectMarketOrder', 'Info', log)
                else:
                    self.sendLogToServer('injectMarketOrder', 'Error', str(respSell))
        elif self.Control_Value < 0:
            OrderQty = self.filo.getOrderValueBuy(self.ASK_PRICE)
            if OrderQty == 0:
                self.sendLogToServer('injectMarketOrders', 'Info_OrderQty', str(OrderQty))
                #print('injectMarketOrders_Info_OrderQty_Buy: ' + str(OrderQty))
            else:
                isSuccsessful, respBuy = self.bmx_curl.setTrailingBuyMarketOrder(OrderQty)
                if isSuccsessful == True and self.Control_Value < 0:
                    self.filo.isSuccessfulOrderValueBuy(OrderQty)
                    self.Control_Value = self.Control_Value + 1
                    log = 'TRADE DOWN '+'-'+str(self.Control_Value)+'-'  + str(self.ASK_PRICE) + '-' + str(OrderQty) + '-' + str(self.availMargin)
                    self.sendLogToServer('injectMarketOrder', 'Info', log)
                else:
                    self.sendLogToServer('injectMarketOrder', 'Error', str(respBuy))
        sleep(0.5)

    ###Margin Thread###
    def getMarginMain(self):
        while True:
            try:
                self.getMargin()
            except Exception as e:
                self.sendLogToServer('getMarginMain', 'Error', str(e.message))

            sleep(self.getMarginDelay)
    def getMargin(self):

        isSucc, availMargin = self.bmx_curl_Margin.getAvailMargin()
        if isSucc == True:
            #print('getMargin: '  +str(availMargin))
            self.availMargin = availMargin
            self.filo.setAvailMargin(self.availMargin)
            # getAvailMarginInfo
            self.sendLogToServer('getAvailMargin', 'Info', str(availMargin))
            #print('getAvailMarginInfo: ' + str(availMargin))
        else:
            print('getMarginError: ' + str(availMargin))

    ###Quotes Thread###
    def getQuotesMain(self):

        while True:
            try:
                self.getQuotes()

            except Exception as e:
                self.sendLogToServer('getQuotesMain', 'Error', str(e.message))
                #print('getQuotesMainError: ' + str('Unable to fetch quotes'))
            sleep(self.getQuotesDelay)
    def getQuotes(self):

        isSucc,bid,ask = self.bmx_curl_Margin.getLatestQuotes()
        if isSucc == True:
            self.BID_PRICE = bid
            self.ASK_PRICE = ask
            #print('self.BID_PRICE: ' + str(self.BID_PRICE))
            #print('self.ASK_PRICE: ' + str(self.ASK_PRICE))
            self.MarketEvents()
            self.sendLogToServer('getQuotesMain', 'Info', str(self.BID_PRICE)+"-"+str(self.ASK_PRICE))
            #print('getQuotesMainInfo: ' + str(self.BID_PRICE)+"-"+str(self.ASK_PRICE))
        else:
            self.sendLogToServer('getQuotesMain', 'Error', str('Unable to fetch quotes'))
            #print('getQuotesMainError: ' + str('Unable to fetch quotes'))

    ###CONNECT TO LOGGING SERVER###
    def writeToLog(self, line):

        log_file = open('./log.txt', 'a')
        log_file.write(line + '\n')
        log_file.close()
    def sendLogToServer(self,logName,logType,logMessage):

        log_message = str(self.PROGRAM_NAME) + '::' + str(logName) + '::' + str(logType) + '::' + str(logMessage)

        try:
            self.writeToLog(log_message)
            #send log messages to your own server below

            #s = socket.socket()  # Create a socket object
            #host = socket.gethostname()  # Get local machine name
            #s.connect((host, self.logging_server_port))
            #s.sendall(log_message)
            #s.close()
        except Exception as e:
            self.writeToLog('Couldn\'t write: ' + str(log_message))
            self.writeToLog(e.message)


MM = Bot()
