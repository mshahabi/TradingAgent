from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.scanner import ScannerSubscription, ScanData
import time
import threading
import os


class TradingApp(EClient,EWrapper):
    def __init__(self):
        EClient.__init__(self, self)  # Initialize EClient with self as the wrapper

    def scannerParameters(self, xml):
        super().scannerParameters(xml)
        open('scanner_parameters.xml', 'w').write(xml)
        print("XML parameters recieved")
    
    def scannerData(self, reqId, rank, contractDetails,distance, benchmark, projecion,legsStr):
        super().scannerData(reqId, rank,contractDetails,distance, benchmark, projecion,legsStr)
        print("Scanner Data is retireved:", reqId, ScanData(contractDetails.contract, rank, distance, benchmark, projecion,legsStr))

# Create an instance of the app and connect to IB Gateway / TWS
def usStkScan(asset_type="STK",asset_loc="STK.NASDAQ", scan_code="HIGH_OPEN_GAP"):
  scan_obj = ScannerSubscription()
  scan_obj.numberOfRows   = 10
  scan_obj.location_code  = asset_loc
  scan_obj.instrument     = asset_type
  scan_obj.scanCode       = scan_code
  return scan_obj

def websocket_con():
    app.run()

app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

con_thread = threading.Thread(target=websocket_con, daemon=True)
# Start a loop to process incoming messages
con_thread.start()
time.sleep(1)
#app.reqScannerParameters()
app.reqScannerSubscription(20, usStkScan(), [], [])

time.sleep(30)
app.cancelScannerSubscription(20)