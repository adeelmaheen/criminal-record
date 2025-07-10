from django.core.management.base import BaseCommand
from scraper.scrapers import EClerksScraper
from scraper.models import CriminalRecord
from django.utils.timezone import now
import logging

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
            default=None
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            help='Maximum number of pages to scrape',
            default=1
        )

    def handle(self, *args, **options):
        try:
            scraper = EClerksScraper(headless=False)
            records = scraper.run(
                from_date=options['from_date'],
                to_date=options['to_date'],
                max_pages=options['max_pages']
            )
            
            saved_count = 0
            for record in records:
                try:
                    CriminalRecord.objects.update_or_create(
                        case_number=record['case_number'],
                        defaults=record
                    )
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving record {record['case_number']}: {str(e)}")
                    continue
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully processed {len(records)} records. Saved/updated {saved_count} records."
            ))
        except Exception as e:
            logger.error(f"Scraper command failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

