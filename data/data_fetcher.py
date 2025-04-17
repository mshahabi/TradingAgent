
from ibapi.contract import Contract
# Define contract function
def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    """
    Creates and returns a Contract object for a US technology stock.

    Args:
        symbol (str): The ticker symbol of the stock.
        sec_type (str, optional): The security type. Defaults to "STK" (stock).
        currency (str, optional): The currency of the stock. Defaults to "USD".
        exchange (str, optional): The exchange where the stock is traded. Defaults to "SMART".

    Returns:
        Contract: A configured Contract object representing the specified stock.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

# Request historical data
def histData(app, req_num, contract, endDate, duration, candle_size):
    """
    Fetches historical market data for a given contract using the Interactive Brokers API.

    Parameters:
        app (ib_insync.IB): The IB application instance used to send the request.
        req_num (int): The unique request ID for the historical data query.
        contract (ib_insync.Contract): The contract object specifying the financial instrument.
        endDate (str): The end date and time for the historical data in the format 'YYYYMMDD HH:MM:SS'.
        duration (str): The duration of the historical data to fetch (e.g., '1 D', '1 W', '1 M').
        candle_size (str): The size of each bar in the historical data (e.g., '1 min', '5 mins', '1 hour').

    Returns:
        None: The function sends a request to fetch historical data but does not return any value.
    """
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime=endDate,
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='TRADES',
                          useRTH=0, # for historical data, useRTH=0 to get pre & after hours data
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[]) 