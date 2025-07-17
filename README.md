# Criminal Records Automation Tool

A Django-based web application that automates the collection of criminal records from eclerksla.com (Louisiana's electronic clerk system) and provides a user-friendly interface for viewing and managing the data.

## Features

- **Web scraping** of criminal records from eclerksla.com
- **Django admin interface** for data management
- **Responsive frontend** with search and filtering capabilities
- **Pagination** for large datasets
- **Detailed record views** with comprehensive information
- **CSV export** functionality
- **Robust error handling** and logging

## Setup Instructions

### Prerequisites

- Python 3.8+
- Chrome browser (for web scraping)
- eClerks LA account credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd criminal-record
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file with your credentials**
   ```bash
   # Copy the example file and edit with your credentials
   cp .env.example .env
   
   # Edit .env file with your actual credentials:
   ECLERKS_EMAIL=your_email@example.com
   ECLERKS_PASSWORD=your_password
   ```

5. **Run database migrations**
   ```bash
   cd crimrec
   python manage.py migrate
   ```

6. **Create superuser (optional for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

## Usage

### Running the Scraper

The scraper now includes improved error handling and stability:

```bash
# Basic usage
# Run in headless mode (no browser window)
python manage.py run_scraper --from-date 01/01/2020 --to-date 01/07/2025 --max-pages 2 --headless

# Using uv (if available)
uv run python manage.py run_scraper --from-date 01/01/2020 --to-date 01/07/2025 --max-pages --headless 2
```

**Command Options:**
- `--from-date`: Start date for search (MM/DD/YYYY)
- `--to-date`: End date for search (MM/DD/YYYY, defaults to current date)
- `--max-pages`: Maximum number of pages to scrape
- `--headless`: Run browser in headless mode

### Running the Web Interface

```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the web interface.

### Running Tests

```bash
python manage.py test
```

## Recent Improvements

### Fixed Issues:
1. **Type Error**: Fixed "'bool' object is not iterable" error in management command
2. **Chrome Driver Stability**: Improved WebDriver setup with better error handling
3. **Logging**: Enhanced logging configuration with proper formatters
4. **Security**: Added environment variable support for sensitive settings
5. **Error Handling**: Added comprehensive error handling throughout the scraper

### Enhanced Features:
- **Credential Validation**: Validates environment variables before starting
- **Retry Logic**: Chrome driver initialization with retry mechanism
- **Better Timeouts**: Increased timeouts for website interactions
- **Improved Date Parsing**: Support for multiple date formats
- **Progress Reporting**: Better progress feedback during scraping
- **Test Coverage**: Added basic test suite for core functionality

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required
ECLERKS_EMAIL=your_email@example.com
ECLERKS_PASSWORD=your_password

# Optional
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues:

1. **Chrome Driver Issues**
   - Ensure Chrome browser is installed
   - Try running with `--headless` flag
   - Check that no other browser instances are running

2. **Login Failures**
   - Verify credentials in `.env` file
   - Check if eClerks website is accessible
   - Ensure account is not locked

3. **Website Structure Changes**
   - The scraper may need updates if the website structure changes
   - Check logs for specific error messages

### Debugging:

- Check `debug.log` for detailed error messages
- Run with `DEBUG=True` in `.env` for verbose output
- Use `--headless=False` to see browser interactions

## Project Structure

```
crimrec/
├── crimrec/          # Django project settings
├── scraper/          # Main application
│   ├── models.py     # Database models
│   ├── scrapers.py   # Web scraping logic
│   ├── views.py      # Web interface views
│   ├── admin.py      # Admin interface
│   └── templates/    # HTML templates
├── requirements.txt  # Dependencies
└── README.md        # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and research purposes only. Ensure compliance with website terms of service and applicable laws when using this tool.

