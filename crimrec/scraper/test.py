#!/usr/bin/env python3
"""
Simple test script to run the EClerks scraper with proper environment variable setup
"""

import os
import sys
from scrapers import EClerksScraper

# Set environment variables directly in the script
os.environ['ECLERKS_EMAIL'] = 'your_email@example.com'  # Replace with your actual email
os.environ['ECLERKS_PASSWORD'] = 'your_password'  # Replace with your actual password

def main():
    try:
        print("Starting EClerks scraper...")
        
        # Create scraper instance
        scraper = EClerksScraper(headless=False)  # Set to True for headless mode
        
        # Run the scraper
        records = scraper.run(
            from_date="01/01/2020",
            to_date="01/07/2025", 
            max_pages=1
        )
        
        print(f"Scraping completed. Found {len(records)} records.")
        
        if records:
            print("\nFirst few records:")
            for i, record in enumerate(records[:3]):
                print(f"Record {i+1}: {record.get('case_number', 'N/A')} - {record.get('defendant_name', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 