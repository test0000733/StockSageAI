import os
import sys

# Ensure the StockSageAI package is on the import path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "StockSageAI"))

from StockSageAI.app import main

if __name__ == "__main__":
    main()
