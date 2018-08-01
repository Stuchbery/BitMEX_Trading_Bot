import socket
import time
import hashlib
import hmac
import json
import uuid
import pycurl
from threading import Thread
from StringIO import StringIO
import cStringIO

class BITMEX_API_CURL:
    def __init__(self,DELTA_SRV_HOST,DELTA_SRV_PORT,logging_server_port,PROGRAM_NAME,API_ENDPOINT,API_KEY,API_SECRET,SYMBOL):
        self.DELTA_SRV_HOST     = DELTA_SRV_HOST
        self.DELTA_SRV_PORT     = DELTA_SRV_PORT
        self.logging_server_port = logging_server_port
        self.PROGRAM_NAME       = PROGRAM_NAME
        self.API_ENDPOINT       = 'https://'+ API_ENDPOINT
        self.SYMBOL             = SYMBOL
        self.API_KEY            = API_KEY
        self.API_SECRET         = API_SECRET
        self.UA_STR             = "p_Stgg_Ord/v2"
        self.requestsRemaining  = 150


        #self.c                  = pycurl.Curl()
        #self.LEV_MULTI          = 0
        #self.init_curl()

    ###
    def setSellMarketOrder(self, orderQty):
        BT1_BT = {}

        BT1_BT['symbol'] = self.SYMBOL
        BT1_BT['side'] = 'Sell'
        BT1_BT['ordType'] = 'Market'
        BT1_BT['timeInForce'] = 'ImmediateOrCancel'
        BT1_BT['orderQty'] = orderQty

        Orders_json_string = json.dumps(BT1_BT)

        resp = self.sendOrder_curl(Orders_json_string)
        if 'error' in str(resp):
            return False, resp
        elif 'Canceled' in str(resp) or 'Rejected' in str(resp):
            return False, resp
        elif 'Filled' in str(resp):
            return True, resp
        else:
            return False, resp
    def setBuyMarketOrder(self, orderQty):
        BT1_BT = {}

        BT1_BT['symbol'] = self.SYMBOL
        BT1_BT['side'] = 'Buy'
        BT1_BT['ordType'] = 'Market'
        BT1_BT['timeInForce'] = 'ImmediateOrCancel'
        BT1_BT['orderQty'] = orderQty

        Orders_json_string = json.dumps(BT1_BT)

        resp = self.sendOrder_curl(Orders_json_string)
        if 'error' in str(resp):
            return False, resp
        elif 'Canceled' in str(resp) or 'Rejected' in str(resp):
            return False, resp
        elif 'Filled' in str(resp):
            return True, resp
        else:
            return False, resp

    def setTrailingSellMarketOrder(self, orderQty):
        BT1_BT = {}

        BT1_BT['symbol'] = self.SYMBOL
        BT1_BT['side'] = 'Sell'
        BT1_BT['ordType'] = 'Stop'  # LimitIfTouched,MarketIfTouched
        BT1_BT['timeInForce'] = 'GoodTillCancel'
        BT1_BT['orderQty'] = orderQty
        BT1_BT['pegPriceType'] = 'TrailingStopPeg'  # LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, TrailingStopPeg.
        BT1_BT['pegOffsetValue'] = -5
        BT1_BT['execInst'] = 'LastPrice'

        Orders_json_string = json.dumps(BT1_BT)

        resp = self.sendOrder_curl(Orders_json_string)
        #print(resp)
        if 'error' in str(resp):
            time.sleep(1)
            return False, resp
        elif 'Canceled' in str(resp) or 'Rejected' in str(resp):
            return False, resp
        elif 'Filled' in str(resp) or 'New' in str(resp):
            return True, resp
        else:
            return False, resp
    def setTrailingBuyMarketOrder(self, orderQty):
        BT1_BT = {}

        BT1_BT['symbol'] = self.SYMBOL
        BT1_BT['side'] = 'Buy'
        BT1_BT['ordType'] = 'Stop'  # LimitIfTouched,MarketIfTouched
        BT1_BT['timeInForce'] = 'GoodTillCancel'
        BT1_BT['orderQty'] = orderQty
        BT1_BT['pegPriceType'] = 'TrailingStopPeg'  # ,LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, TrailingStopPeg.
        BT1_BT['pegOffsetValue'] = 5
        BT1_BT['execInst'] = 'LastPrice'
        # BT1_BT['stopPx'] = 6600

        #

        Orders_json_string = json.dumps(BT1_BT)

        resp = self.sendOrder_curl(Orders_json_string)
        #print(resp)
        if 'error' in str(resp):
            time.sleep(1)
            return False, resp
        elif 'Canceled' in str(resp) or 'Rejected' in str(resp):
            return False, resp
        elif 'Filled' in str(resp) or 'New' in str(resp):
            return True, resp
        else:
            return False, resp

    ###METHODS THAT USE THE API REQUESTS###
    def sendOrder_curl(self, postData):
        if int(self.requestsRemaining) > 0:
            try:
                path = '/api/v1/order'
                nonce = self.getNonce()

                message = 'POST' + path + str(nonce) + str(postData)

                signature = self.genSig(self.API_SECRET, message)
                headers = []
                headers.append("Accept: application/json")
                headers.append("Content-Type: application/json")
                headers.append("api-nonce: " + str(nonce))
                headers.append("api-key: " + str(self.API_KEY))
                headers.append("api-signature: " + str(signature))

                buffer = StringIO()
                buf = cStringIO.StringIO()

                c = pycurl.Curl()
                c.setopt(c.URL, self.API_ENDPOINT+"/api/v1/order")
                c.setopt(c.WRITEDATA, buffer)
                c.setopt(c.HEADERFUNCTION, buf.write)
                c.setopt(c.SSL_VERIFYPEER, 0)
                c.setopt(c.SSL_VERIFYHOST, 0)
                c.setopt(c.CUSTOMREQUEST, "POST")
                c.setopt(c.VERBOSE, 1)
                c.setopt(c.USERAGENT, self.UA_STR)

                c.setopt(c.HTTPHEADER, headers)
                c.setopt(c.POSTFIELDS, postData)

                c.perform()
                body = buffer.getvalue()
                jsonbody = json.loads(body)
                #sendOrder_curl_Info
                self.sendLogToServer('sendOrder_curl', 'Info', str(jsonbody))

                resp_headers = self.getRespHeaderDict(buf.getvalue())
                self.requestsRemaining = resp_headers['X-RateLimit-Remaining']
                # curl_requestsRemaining_Info
                self.sendLogToServer('curl_requestsRemaining', 'Info', str(self.requestsRemaining))

                c.close()
                return jsonbody

            except Exception as e:
                # sendOrder_curl_Error
                self.sendLogToServer('sendOrder_curl', 'Error', str(e.message))
                c.close()
                #self.init_curl()
                return 'error ' + str(e.message)
        else:
            time.sleep(6)
            self.requestsRemaining = self.requestsRemaining + 1
            self.sendLogToServer('curl_requestsRemaining', 'Error', str(self.requestsRemaining))
            return 'error requestsRemaining = ' + str(self.requestsRemaining)
    def getAvailMargin(self):
        #https://www.bitmex.com/api/v1/user/margin?currency=XBt
        if int(self.requestsRemaining) > 0:

            try:
                #https://www.bitmex.com/api/v1/order?symbol=XBTUSD&filter=%7B%22open%22%3A%20true%7D&count=100&reverse=true'
                buffer = StringIO()
                buf = cStringIO.StringIO()

                url = self.API_ENDPOINT+"/api/v1/user/margin?currency=XBt"
                path = "/api/v1/user/margin?currency=XBt"
                #request = {}
                #request['currency'] = 'XBt'
                # request['currency'] = self.LEV_MULTI

                #json_string = json.dumps(request)
                # print('json_string: ' + str(json_string))
                c = pycurl.Curl()
                c.setopt(c.URL, url)  # ?currency=XBt
                c.setopt(c.WRITEDATA, buffer)
                c.setopt(c.HEADERFUNCTION, buf.write)
                c.setopt(c.SSL_VERIFYPEER, 0)
                c.setopt(c.SSL_VERIFYHOST, 0)
                c.setopt(c.CUSTOMREQUEST, "GET")
                c.setopt(c.VERBOSE, 1)
                c.setopt(c.USERAGENT, self.UA_STR)

                nonce = self.getNonce()
                # verb + path + str(nonce) + data
                message = 'GET' + path + str(nonce)

                signature = self.genSig(self.API_SECRET, message)

                headers = []
                headers.append("Accept: application/json")
                headers.append("Content-Type: application/json")
                headers.append("api-nonce: " + str(nonce))
                headers.append("api-key: " + str(self.API_KEY))
                headers.append("api-signature: " + str(signature))

                c.setopt(c.HTTPHEADER, headers)
                # c.setopt(c.POSTFIELDS, json_string)

                c.perform()
                body = buffer.getvalue()
                json_obj = json.loads(body)
                self.sendLogToServer('getAvailMarginCurl', 'Info', str(json_obj))

                resp_headers = self.getRespHeaderDict(buf.getvalue())
                self.requestsRemaining = resp_headers['X-RateLimit-Remaining']
                # curl_requestsRemaining_Info
                self.sendLogToServer('curl_requestsRemaining', 'Info', str(self.requestsRemaining))

                c.close()
                if 'error' in str(json_obj):
                    return False, json_obj
                else:
                    try:
                        return True, int(json_obj['availableMargin'])
                    except Exception as e:
                        self.sendLogToServer('getAvailMarginCurl', 'Error', str(e.message))
                        return False, str(e.message)

            except Exception as e:
                self.sendLogToServer('getAvailMarginCurl', 'Error', str(e.message))
                return False, str(e.message)
        else:
            time.sleep(6)
            self.requestsRemaining = self.requestsRemaining + 1
            self.sendLogToServer('curl_requestsRemaining', 'Error', str(self.requestsRemaining))
            return False, 'error requestsRemaining = ' + str(self.requestsRemaining)
    def getLatestQuotes(self):
        #https://www.bitmex.com/api/v1/user/margin?currency=XBt
        try:
            #https://www.bitmex.com/api/v1/order?symbol=XBTUSD&filter=%7B%22open%22%3A%20true%7D&count=100&reverse=true'
            buffer = StringIO()
            buf = cStringIO.StringIO()

            url = "http://"+str(self.DELTA_SRV_HOST)+":"+str(self.DELTA_SRV_PORT)+"/quote?symbol=XBTUSD"
            path = "/quote?symbol=XBTUSD"
            #request = {}
            #request['currency'] = 'XBt'
            # request['currency'] = self.LEV_MULTI

            #json_string = json.dumps(request)
            # print('json_string: ' + str(json_string))
            c = pycurl.Curl()
            c.setopt(c.URL, url)  # ?currency=XBt
            c.setopt(c.WRITEDATA, buffer)
            c.setopt(c.HEADERFUNCTION, buf.write)
            c.setopt(c.SSL_VERIFYPEER, 0)
            c.setopt(c.SSL_VERIFYHOST, 0)
            c.setopt(c.CUSTOMREQUEST, "GET")
            c.setopt(c.VERBOSE, 0)
            c.setopt(c.USERAGENT, self.UA_STR)

            nonce = self.getNonce()
            # verb + path + str(nonce) + data
            message = 'GET' + path + str(nonce)

            signature = self.genSig(self.API_SECRET, message)

            headers = []
            headers.append("Accept: application/json")
            headers.append("Content-Type: application/json")
            headers.append("api-nonce: " + str(nonce))
            headers.append("api-key: " + str(self.API_KEY))
            headers.append("api-signature: " + str(signature))

            c.setopt(c.HTTPHEADER, headers)
            # c.setopt(c.POSTFIELDS, json_string)

            c.perform()
            body = buffer.getvalue()
            json_obj = json.loads(body)[-1]
            bid_price = float(json_obj['bidPrice'])
            ask_price = float(json_obj['askPrice'])
            c.close()
            self.sendLogToServer('getLatestQuotes', 'Info', str(bid_price)+"::"+ str(ask_price))
            return True,bid_price,ask_price


        except Exception as e:
            self.sendLogToServer('getLatestQuotes', 'Error', str(e.message))
            return False, 0,0

    ###HELPER FUNC###
    def getWSAuthKey(self):
        nonce = self.getNonce()
        message = 'GET/realtime' + str(nonce)
        signature = self.genSig(self.API_SECRET, message)

        ret_dict = {"op": "authKey", "args": [self.API_KEY, nonce, signature]}
        return ret_dict
    def getNonce(self):
        #time.sleep(0.1)
        """Generate pseudo-random number and seconds since epoch (UTC)."""
        #nonce = uuid.uuid1()
        #oauth_timestamp = str(nonce.time)
        #, oauth_nonce= nonce.hex
        #return int(oauth_timestamp)/100
        return int(time.time()*1000)
    def getRespHeaderDict(self, header):
        str_val = ''
        resp_headers = {}
        for char in header:
            str_val = str_val + char
            # print ('str: ' + str(str_val))
        strArray = str_val.split('\r\n')
        # print ('strArray: ' + str(strArray))
        for line in strArray:
            if ': ' in line:
                arr = line.split(': ')
                resp_headers[arr[0]] = arr[1]


        return resp_headers
        # print ('X-RateLimit-Limit       : ' + str(resp_headers['X-RateLimit-Limit']))
        # print ('X-RateLimit-Remaining   : ' + str(resp_headers['X-RateLimit-Remaining']))
        # print ('X-RateLimit-Reset       : ' + str(resp_headers['X-RateLimit-Reset']))
    def genSig(self, API_SECRET, message):
        # message = verb + path + str(nonce) + data
        message = bytes(message).encode('utf-8')
        # print("Computing HMAC: %s" % message)

        signature = hmac.new(API_SECRET, message, digestmod=hashlib.sha256).hexdigest()
        # print("signature: " + str(signature))

        return signature
    def getRequestsRemaining(self):
        return self.requestsRemaining

    ###CONNECT TO LOGGING SERVER###
    def writeLogErrors(self, line):

        log_file = open('./log_curl.txt', 'a')
        log_file.write(line + '\n')
        log_file.close()
    def sendLogToServer(self,logName,logType,logMessage):
        try:
            log = str(self.PROGRAM_NAME) + '::' + str(logName) + '::' + str(logType) + '::' + str(logMessage)
            self.writeLogErrors(log)
            #send log messages to your own server below

            #s = socket.socket()  # Create a socket object
            #host = socket.gethostname()  # Get local machine name
            #s.connect((host, self.logging_server_port))
            #s.sendall(log)
            #s.close()

        except Exception as e:
            self.writeLogErrors(e.message)


