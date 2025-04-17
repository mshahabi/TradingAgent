import threading
import time

import pandas as pd
import streamlit as st
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.hist_data = {}
        self.data_event = threading.Event()

    def historicalData(self, reqId, bar):
        new_data = pd.DataFrame(
            [
                {
                    "Date": bar.date,
                    "Open": bar.open,
                    "High": bar.high,
                    "Low": bar.low,
                    "Close": bar.close,
                    "Volume": bar.volume,
                }
            ]
        )

        if reqId not in self.hist_data or len(self.hist_data[reqId]) == 0:
            self.hist_data[reqId] = new_data
        else:
            self.hist_data[reqId] = pd.concat(
                [self.hist_data[reqId], new_data], ignore_index=True
            )

    def historicalDataEnd(self, reqId, startDateStr, endDateStr):
        print(
            f"Historical data fetch completed for ReqId: {reqId}, Start: {startDateStr}, End: {endDateStr}"
        )
        self.data_event.set()  # Signal that data fetching is complete

    def check_connection(self):
        return self.isConnected()

    def stop_connection(self):
        self.disconnect()


def usStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def fetch_historical_data(app, symbol):
    if not app.check_connection():
        st.error("Not connected to IBKR. Please check the connection.")
        return

    contract = usStk(symbol)
    app.reqHistoricalData(
        reqId=1,
        contract=contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="5 mins",
        whatToShow="TRADES",
        useRTH=1,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[],
    )
    app.data_event.wait()  # Wait for the data fetching to complete
    app.data_event.clear()


def start_ibkr_connection(app):
    app.run()


if __name__ == "__main__":

    def initialize_ibkr_connection():
        app = TradeApp()
        import random

        unique_client_id = random.randint(1000, 9999)  # Generate a unique client ID
        app.connect("127.0.0.1", 7497, clientId=unique_client_id)

        # Start the IBKR connection in a separate thread
        api_thread = threading.Thread(target=start_ibkr_connection, args=(app,))
        api_thread.start()
        return app

    app = initialize_ibkr_connection()  # Initialize the app instance
    time.sleep(1)  # Allow time for connection to establish

    # Streamlit app
    st.title("IBKR Historical Data Viewer")
    symbol = st.text_input("Enter Stock Symbol", value="AAPL")
    fetch_button = st.button("Fetch Historical Data")
    stop_button = st.button("Stop Connection")

    if fetch_button:
        with st.spinner("Fetching data..."):
            data_thread = threading.Thread(
                target=fetch_historical_data, args=(app, symbol)
            )
            data_thread.start()
            data_thread.join()  # Wait for the data fetching thread to complete

        if 1 in app.hist_data:
            st.write(f"Historical Data for {symbol}")
            st.dataframe(app.hist_data[1])
        else:
            st.write("No historical data available.")

    if stop_button:
        app.stop_connection()
        st.success("Disconnected from IBKR.")
