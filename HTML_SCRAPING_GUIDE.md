# HTML Form Scraping Guide

## Overview

The HTML Form Scraping feature automates the collection of greyhound racing data from web sources, eliminating the need to manually download PDF files. This feature is designed to integrate seamlessly with the existing analytics pipeline.

## Components

### 1. Scraper Script (`scrape_html_forms.py`)

The main scraping script that:
- Fetches HTML data from configured sources
- Parses race form information
- Converts data to CSV format compatible with the pipeline
- Supports mock data generation for testing

### 2. GitHub Actions Workflow (`.github/workflows/scrape-and-analyze.yml`)

An automated workflow that:
- Runs daily at 6 AM UTC
- Scrapes latest race forms
- Processes data through the analytics pipeline
- Uploads results as artifacts
- Can be triggered manually on-demand

## Quick Start

### Testing with Mock Data

The scraper includes a mock data generator for testing without accessing real websites:

```bash
# Generate mock data
python scrape_html_forms.py --mock --output-dir data_predictions

# Process mock data through pipeline
python main.py data_predictions/*.csv
```

### Configuring Real Data Sources

To scrape actual greyhound racing websites, edit `scrape_html_forms.py`:

1. **Update the base URL:**
```python
SCRAPING_CONFIG = {
    "base_url": "https://actual-greyhound-racing-site.com",
    # ...
}
```

2. **Configure endpoints:**
```python
"endpoints": {
    "race_form": "/api/races",  # Update with actual endpoint
    "results": "/api/results"
}
```

3. **Customize the HTML parser:**

Update the `parse_html_race_form()` function to match the HTML structure of your target website:

```python
def parse_html_race_form(soup):
    races = []

    # Example: Find all race containers
    race_containers = soup.find_all('div', class_='actual-race-class')

    for race_container in race_containers:
        # Extract data based on actual HTML structure
        race_data = {
            'Track': race_container.find('span', class_='track-name').text.strip(),
            'RaceNumber': int(race_container.find('span', class_='race-num').text.strip()),
            # Add more fields as needed
        }
        races.append(race_data)

    return races
```

## Usage

### Command-Line Options

```bash
# Scrape today's data
python scrape_html_forms.py --output-dir data_predictions

# Scrape specific date
python scrape_html_forms.py --date 2025-01-04 --output-dir data_predictions

# Use custom URL
python scrape_html_forms.py --url https://example.com/races --output-dir data_predictions

# Generate mock data for testing
python scrape_html_forms.py --mock --output-dir data_predictions
```

### GitHub Actions Workflow

#### Automated Daily Runs

The workflow automatically runs daily at 6 AM UTC. Results are uploaded as artifacts.

#### Manual Triggering

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Select "Scrape and Analyze Greyhound Forms" workflow
4. Click "Run workflow"
5. Optionally specify:
   - **Date**: Target date (YYYY-MM-DD format)
   - **Use mock data**: Enable for testing without real data

#### Viewing Results

After the workflow completes:
1. Go to the workflow run in the Actions tab
2. Scroll to the "Artifacts" section at the bottom
3. Download:
   - `analysis-results-TIMESTAMP`: Full analysis outputs
   - `selective-picks-TIMESTAMP`: Recommended betting picks

## Output Format

The scraper generates CSV files with the following structure:

```csv
Track,RaceNumber,Box,DogName,Trainer,Distance,StartTime,Grade,DLR
Angle Park,1,1,Thunder Bolt,John Smith,500,20:07,2,120
Angle Park,1,2,Lightning Speed,Jane Doe,500,20:14,3,201
...
```

### Required Columns

- `Track`: Track name (e.g., "Angle Park", "BALLARAT")
- `RaceNumber`: Race number (integer)
- `Box`: Box/trap number (1-8)
- `DogName`: Name of the greyhound
- `Trainer`: Trainer name
- `Distance`: Race distance in meters
- `StartTime`: Start time (HH:MM format)

### Optional Columns

- `Grade`: Dog's grade/class
- `DLR`: Recent form (e.g., "120" for 1st, 2nd, 0th)
- `PrizeMoney`: Career prize money
- Any other fields the parser can extract

## Integration with Pipeline

The scraped CSV files are fully compatible with the existing pipeline:

1. **Place scraped files** in `data_predictions/`
2. **Run analysis:**
```bash
python main.py data_predictions/*.csv
```

3. **Check outputs** in `outputs/`:
   - `todays_form_color.xlsx`: Color-coded analysis
   - `selective_picks.csv`: Recommended bets
   - `picks.csv`: All top picks

## Troubleshooting

### No Data Scraped

**Symptoms:** Empty CSV files or error messages

**Solutions:**
1. Check website URL is correct
2. Verify HTML structure hasn't changed
3. Check internet connectivity
4. Review scraper logs for error details
5. Use `--mock` flag to test pipeline independently

### HTML Parsing Errors

**Symptoms:** `AttributeError` or incomplete data

**Solutions:**
1. Inspect the target website's HTML structure
2. Update CSS selectors in `parse_html_race_form()`
3. Use browser developer tools to identify correct elements
4. Add error handling for missing elements

### GitHub Actions Workflow Fails

**Symptoms:** Workflow shows red X in Actions tab

**Solutions:**
1. Check workflow logs for specific error
2. Verify `requirements.txt` includes all dependencies
3. Test scraper locally first
4. Use `use_mock_data: true` input to isolate issues

## Best Practices

### Data Source Selection

- **Reliability:** Choose stable, well-maintained websites
- **Terms of Service:** Review and comply with website ToS
- **Rate Limiting:** Add delays between requests if needed
- **Robots.txt:** Respect robots.txt directives

### Error Handling

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error("Request timed out")
    # Fall back to mock data or retry
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed: {e}")
    # Handle error appropriately
```

### Logging

The scraper includes comprehensive logging:
- `INFO`: Normal operation messages
- `WARNING`: Non-critical issues (e.g., missing optional fields)
- `ERROR`: Critical failures that require attention

Check logs in:
- Console output during manual runs
- GitHub Actions workflow logs for automated runs
- `outputs/greyhound_analytics.log` (if pipeline runs)

## Advanced Configuration

### Custom Headers

Some websites require specific headers:

```python
SCRAPING_CONFIG = {
    "headers": {
        "User-Agent": "Mozilla/5.0 ...",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://example.com/"
    }
}
```

### Authentication

If the website requires login:

```python
def scrape_with_auth(url, username, password):
    session = requests.Session()
    login_url = "https://example.com/login"

    # Login
    session.post(login_url, data={
        'username': username,
        'password': password
    })

    # Scrape authenticated pages
    response = session.get(url)
    return response
```

**Note:** Store credentials securely using GitHub Secrets for workflow usage.

### Rate Limiting

Add delays to avoid overwhelming servers:

```python
import time

for race in races:
    scrape_race(race)
    time.sleep(1)  # Wait 1 second between requests
```

## Future Enhancements

Potential improvements:
- [ ] Support multiple data sources
- [ ] Automatic HTML structure detection
- [ ] Caching to reduce redundant requests
- [ ] API integration (if available)
- [ ] Real-time data streaming
- [ ] Historical data archiving

## Security Considerations

- **Sensitive Data:** Never commit API keys, passwords, or tokens to the repository
- **GitHub Secrets:** Use GitHub Secrets for sensitive configuration
- **HTTPS Only:** Always use HTTPS for data transmission
- **Input Validation:** Sanitize all scraped data before processing

## Support

For issues or questions:
1. Check this guide first
2. Review existing GitHub Issues
3. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Relevant log output
   - Environment details (Python version, OS, etc.)
