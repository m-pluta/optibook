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

BASKET_INSTRUMENT_ID = 'SEMIS_ETF_US'
STOCK_INSTRUMENT_IDS = ['C2_SOLAR_CO', 'C2_WIND_LTD']


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


def trade_cycle(e: Exchange):
    # because we use limit orders, always delete existing orders that remain from the previous iteration
    e.delete_orders(BASKET_INSTRUMENT_ID)
    basket_book = e.get_last_price_book(BASKET_INSTRUMENT_ID)
    if basket_book and basket_book.bids and basket_book.asks:
        logger.info(f'Order book for {BASKET_INSTRUMENT_ID}: best bid={basket_book.bids[0].price:.2f}, best ask={basket_book.asks[0].price:.2f}')
        # try to improve the best bid and best ask by 10 cents
        new_bid_price = basket_book.bids[0].price + 0.1
        new_ask_price = basket_book.asks[0].price - 0.1
        if new_ask_price - new_bid_price > 0.01:
            bid_response: InsertOrderResponse = e.insert_order(BASKET_INSTRUMENT_ID, price=new_bid_price, volume=1, side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
            print_order_response(bid_response)
            ask_response: InsertOrderResponse = e.insert_order(BASKET_INSTRUMENT_ID, price=new_ask_price, volume=1, side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)
            print_order_response(ask_response)
        else:
            logger.info(f'Order book is already too tight to improve further!')
    else:
        logger.info('No top bid/ask or no book at all for the basket instrument')

    print_report(e)


def main():
    exchange = Exchange()
    exchange.connect()

    sleep_duration_sec = 5
    while True:
        trade_cycle(exchange)
        logger.info(f'Iteration complete. Sleeping for {sleep_duration_sec} seconds')
        time.sleep(sleep_duration_sec)


if __name__ == '__main__':
    main()
