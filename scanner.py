from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.scanner import ScannerSubscription, ScanData
import time
import threading
import os
from datetime import datetime

class TradingApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)  # Initialize EClient with self as the wrapper
        self.scanned_data = []  # List to store scanned data
    def scannerParameters(self, xml):
        super().scannerParameters(xml)
        open('scanner_parameters.xml', 'w').write(xml)
        print("XML parameters received")

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark, projection, legsStr)
        print("Scanner Data retrieved:", reqId, ScanData(contractDetails.contract, rank, distance, benchmark, projection, legsStr))
        data = {
                "timestamp": datetime.now(),
                "reqId": reqId,
                "rank": rank,
                "contract": contractDetails.contract,
                "distance": distance,
                "benchmark": benchmark,
                "projection": projection,
                "legsStr": legsStr
            }
        self.scanned_data.append(data)
        print("Scanner Data retrieved:", data)
# Create an instance of the app and connect to IB Gateway / TWS
def customStockScan():
    scan_obj = ScannerSubscription()
    scan_obj.numberOfRows = 10
    scan_obj.instrument = "STK"
    scan_obj.locationCode = "STK.US.MAJOR"
    scan_obj.scanCode = "HOT_BY_VOLUME"  # High relative volume
    scan_obj.abovePrice = 1.0
    scan_obj.belowPrice = 20.0
    scan_obj.aboveVolume = 500000  # Minimum volume to ensure liquidity
    scan_obj.marketCapBelow = 100000000  # Float under 100 million shares
    scan_obj.stockTypeFilter = "ALL"
    return scan_obj

def websocket_con():
    app.run()

app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

con_thread = threading.Thread(target=websocket_con, daemon=True)
# Start a loop to process incoming messages
con_thread.start()
time.sleep(1)

# Request scanner subscription with custom criteria
app.reqScannerSubscription(20, customStockScan(), [], [])

time.sleep(30)
app.cancelScannerSubscription(20)
print(app.scanned_data)