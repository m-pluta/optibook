'''
EXAMPLE AUTO TRADER

Do not edit this file directly. Instead, copy it somewhere else in your workspace.
These are simple bots that illustrate the Optibook API and some simple trading concepts. These bots will not make a profit.

This is an example bot that trades a single instrument SEMIS_ETF_US.
All it does is to randomly insert either a BID or an ASK every 5 seconds.
The price at which it inserts is equal to the opposite side of the order book.
Thus, if the best bid in the order book is currently 90, it will send a sell order for price 90.
If the best ask in the order book is 91, it will send a buy order for price 91.

The order type this bot uses is IOC (immediate or cancel). This means that if the order does not
immediately trade, it will not be visible to others in the order book. Instead, it will be cancelled automatically.
'''
import logging
import time
from typing import List
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse
from optibook.synchronous_client import Exchange
import random
import json

logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

US_BASKET_ID = 'SEMIS_ETF_US'
EU_BASKET_ID = 'SEMIS_ETF_EU'
BASKET_INSTRUMENT_ID = 'SEMIS_ETF_US'
STOCK_INSTRUMENT_IDS = ['C2_SOLAR_CO', 'C2_WIND_LTD']

sleep_duration_sec = 1


def print_report(e: Exchange):
    pnl = e.get_pnl()
    positions = e.get_positions()
    my_trades = e.poll_new_trades(BASKET_INSTRUMENT_ID)
    all_market_trades = e.poll_new_trade_ticks(BASKET_INSTRUMENT_ID)
    logger.info(f'I have done {len(my_trades)} trade(s) in {BASKET_INSTRUMENT_ID} since the last report. There have been {len(all_market_trades)} market trade(s) in total in {BASKET_INSTRUMENT_ID} since the last report.')
    logger.info(f'My PNL is: {pnl:.2f}')
    logger.info(f'My current positions are: {json.dumps(positions, indent=3)}')


def print_order_response(order_response: InsertOrderResponse):
    if order_response.success:
        logger.info(f"Inserted order successfully, order_id='{order_response.order_id}'")
    else:
        logger.info(f"Unable to insert order with reason: '{order_response.success}'")

def get_largest_bid_pricevolume(pricebook):
    if not pricebook.bids:
        return None  # Return None if there are no bids

    return max(pricebook.bids, key=lambda pv: pv.price)

def get_smallest_ask_pricevolume(pricebook):
    if not pricebook.asks:
        return None  # Return None if there are no bids

    return min(pricebook.asks, key=lambda pv: pv.price)

class OrderEngine:
    def __init__(self):
        self.exchange = Exchange()
        self.exchange.connect()
    
    def make_order(self, instrument_id, price, vol, side, order_type):
        #Total position (positive or negative) per instrument cannot go over 750 lots

        self.exchange.insert_order(instrument_id, price, vol, side, order_type)

        

def trade_cycle(e: Exchange):
    # this is the main bot logic which gets called every 5 seconds
    # fetch the current order book
    us_basket_book = e.get_last_price_book(US_BASKET_ID)
    eu_basket_book = e.get_last_price_book(EU_BASKET_ID)

    us_bid_pricevol = get_largest_bid_pricevolume(us_basket_book)
    us_ask_pricevol = get_smallest_ask_pricevolume(us_basket_book)

    eu_bid_pricevol = get_largest_bid_pricevolume(eu_basket_book)
    eu_ask_pricevol = get_smallest_ask_pricevolume(eu_basket_book)

    if us_bid_pricevol and us_ask_pricevol and eu_bid_pricevol and eu_ask_pricevol:
        if us_bid_pricevol.price > eu_ask_pricevol.price:
            print("a")
            vol = 1
            buyResponse = e.insert_order(EU_BASKET_ID, price=eu_ask_pricevol.price, volume=vol, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            sellResponse = e.insert_order(US_BASKET_ID, price=us_bid_pricevol.price, volume=vol, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            print(f"ARB {eu_ask_pricevol.price} @ {us_bid_pricevol.price} | Vol {vol}")
            print(buyResponse)
            print(sellResponse)
                
        elif eu_bid_pricevol.price > us_ask_pricevol.price:
            print("b")
            vol = 1
            buyResponse = e.insert_order(US_BASKET_ID, price=us_ask_pricevol.price, volume=vol, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            sellResponse = e.insert_order(EU_BASKET_ID, price=eu_bid_pricevol.price, volume=vol, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            print(f"ARB {us_ask_pricevol.price} @ {eu_bid_pricevol.price} | Vol {vol}")
            print(buyResponse)
            print(sellResponse)
        else:
            print("nothing")
    else:
        print("some market is closed")

    """
    # verify that the book exists and that it has at least one bid and ask
    if basket_book and basket_book.bids and basket_book.asks:
        # now randomly either shoot a BID (buy order) or an ASK (sell order)
        if random.random() < 0.5:
            response: InsertOrderResponse = e.insert_order(BASKET_INSTRUMENT_ID, price=basket_book.asks[0].price, volume=1, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
        else:
            response: InsertOrderResponse = e.insert_order(BASKET_INSTRUMENT_ID, price=basket_book.bids[0].price, volume=1, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
        # now look at whether you successfully inserted an order or not.
        # note: If you send invalid information, such as in instrument which does not exist, you will be disconnected
        print_order_response(response)
    else:
        logger.info('No top bid/ask or no book at all for the basket instrument')
    print_report(e)

    """


def main():
    exchange = Exchange()
    exchange.connect()

    # you can also define host/user/pass yourself
    # when not defined, it is taken from ~/.optibook file if it exists
    # if that file does not exists, an error is thrown
    #exchange = Exchange(host='host-to-connect-to', info_port=7001, exec_port=8001, username='your-username', password='your-password')
    #exchange.connect()

    while True:
        trade_cycle(exchange)
        logger.info(f'Iteration complete. Sleeping for {sleep_duration_sec} seconds')
        time.sleep(sleep_duration_sec)


if __name__ == '__main__':
    main()
