from django.core.management.base import BaseCommand
from scraper.scrapers import EClerksScraper
from scraper.models import CriminalRecord
from django.utils.timezone import now
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the eClerksLA criminal records scraper'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-date',
            type=str,
            help='Start date for search (MM/DD/YYYY)',
            default='01/01/2020'
        )
        parser.add_argument(
            '--to-date',
            type=str,
            help='End date for search (MM/DD/YYYY)',
            default=datetime.now().strftime('%m/%d/%Y')
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            help='Maximum number of pages to scrape',
            default=1
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting criminal records scraper...'))
        
        try:
            scraper = EClerksScraper(headless=options['headless'])
            
            # Get initial record count
            initial_count = CriminalRecord.objects.count()
            
            success = scraper.run(
                from_date=options['from_date'],
                to_date=options['to_date'],
                max_pages=options['max_pages']
            )
            
            if success:
                # Get final record count and records scraped
                final_count = CriminalRecord.objects.count()
                records_added = final_count - initial_count
                total_records_scraped = len(scraper.records)
                
                self.stdout.write(self.style.SUCCESS(
                    f"Scraping completed successfully!\n"
                    f"Records scraped: {total_records_scraped}\n"
                    f"Records added to database: {records_added}\n"
                    f"Total records in database: {final_count}"
                ))
            else:
                self.stdout.write(self.style.ERROR("Scraping failed. Check logs for details."))
                
        except Exception as e:
            logger.error(f"Scraper command failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

