# Criminal Records Automation Tool

## Setup Instructions

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install required packages:
   ```bash
   pip install -r requirements.txt

4. Create .env file with your eClerksLA credentials:
   ```bash
    ECLERKS_EMAIL=your_email@example.com
    ECLERKS_PASSWORD=your_password

5. Run migrations:
    ```bash
    python manage.py migrate

6. Create superuser (optional for admin access):
    ```bash
    python manage.py createsuperuser

## Running the Scraper
    ```bash
   
    python manage.py run_scraper --from-date 01/01/2020 --to-date 01/07/2025 --max-pages 2
    
    ```bash

## Running the Development Server
    ```bash
    python manage.py runserver

## Features
- Web scraping of criminal records from eclerksla.com

- Django admin interface for data management

- Responsive frontend with search and filtering

- Pagination for large datasets

- Detailed record views

