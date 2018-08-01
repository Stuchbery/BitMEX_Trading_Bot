import math


class FILO_ORDERS:


    def __init__(self,availMargin,OrderQtyPercentage):
        #self.stack = ["a", "b", "c"]
        self.availMargin = availMargin
        self.OrderQtyPercentage = OrderQtyPercentage

    def setAvailMargin(self,availMargin):
        self.availMargin = availMargin

    def calcOrderQty(self,price):
        orderQty_USD = (float(self.availMargin) / float(100000000)) * float(price)
        orderQty_USD = (orderQty_USD / 100.00) * self.OrderQtyPercentage
        orderQty_USD = math.ceil(orderQty_USD)
        return orderQty_USD

    def getOrderValue(self,side,price):

        #self.calcOrderQty(price)
        pass
    def writeBuyQueue(self, my_list):
        with open('./Buy_Queue.txt', 'w') as f:
            for s in my_list:
                f.write(str(s) + '\n')
            f.close()
    def writeSellQueue(self, my_list):
        with open('./Sell_Queue.txt', 'w') as f:
            for s in my_list:
                f.write(str(s) + '\n')
            f.close()

    def appendBuyQueue(self, new_Val):
        with open('./Buy_Queue.txt', 'a') as f:
            f.write(str(new_Val) + '\n')
            f.close()
    def appendSellQueue(self, new_Val):
        with open('./Sell_Queue.txt', 'a') as f:
            f.write(str(new_Val)+ '\n')
            f.close()
    def readBuyQueue(self):
        with open('./Buy_Queue.txt', 'r') as f:
            my_list = [line.rstrip('\n') for line in f]
        f.close()
        return my_list

        # log_file = open('./Buy_Queue.txt', 'a')
        # log_file.write(line + '\n')
        # log_file.close()
    def readSellQueue(self):
        with open('./Sell_Queue.txt', 'r') as f:
            my_list = [line.rstrip('\n') for line in f]
        f.close()
        return my_list

        #log_file = open('./Buy_Queue.txt', 'a')
        #log_file.write(line + '\n')
        #log_file.close()
    def getBuyQueueLength(self):
        return len(self.readBuyQueue())
    def getSellQueueLength(self):
        return len(self.readSellQueue())

    def getOrderValueSell(self, ASK_PRICE):

        if self.getBuyQueueLength() > 0:
            #fetch and remove last buy price from BUY QUEUE
            buyQueueLst = self.readBuyQueue()
            orderQty = int(buyQueueLst[-1])
            return orderQty
        else:
            #new sell value
            orderQty = self.calcOrderQty(ASK_PRICE)
            return int(orderQty)

    def isSuccessfulOrderValueSell(self, orderQty):
        if self.getBuyQueueLength() > 0:
            buyQueueLst = self.readBuyQueue()
            self.writeBuyQueue(buyQueueLst[:-1])
        else:
            # save to sell queue
            self.appendSellQueue(orderQty)

    def getOrderValueBuy(self, ASK_PRICE):

        if self.getSellQueueLength() > 0:
            #fetch and remove last buy price from SELL QUEUE
            sellQueueLst = self.readSellQueue()
            orderQty = int(sellQueueLst[-1])
            return orderQty
        else:
            #new buy value
            orderQty = self.calcOrderQty(ASK_PRICE)
            return int(orderQty)

    def isSuccessfulOrderValueBuy(self, orderQty):
        if self.getSellQueueLength() > 0:
            sellQueueLst = self.readSellQueue()
            self.writeSellQueue(sellQueueLst[:-1])
        else:
            # save to sell queue
            self.appendBuyQueue(orderQty)



#obj = FILO_ORDERS(2000000,3)

#my_list = obj.readBuyQueue()
#print(str(my_list))
'''
stack = ["a", "b", "c"]

# add an element to the end of the list
stack.append("e")
stack.append("f")
print stack

# pop operation
stack.pop()
print stack

# pop operation
stack.pop()
print stack

# push operation
stack.append("d")
print stack
'''