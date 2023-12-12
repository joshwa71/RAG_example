import os
import sys
import requests
from bs4 import BeautifulSoup
import argparse
import html2text
from urllib.parse import urlparse, urljoin
import pandas as pd

def process_html_2_text(input_dir, output_dir, company, category):
    # Initialize html2text converter
    h = html2text.HTML2Text()
    h.ignore_links = True

    # Traverse through the directory structure
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.html'):
                # Compute file paths
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path.replace('.html', '.txt'))

                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Read and convert HTML file to text
                with open(input_path, 'r', encoding='utf-8') as infile:
                    html_content = infile.read()
                    text_content = h.handle(html_content)

                # Add company and category information at the beginning
                header = f"{company}, {category}\n"
                full_text = header + text_content

                # Write the processed text to file
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(full_text)

def is_valid_url(url):
    """ Check if a URL is valid by parsing its scheme and network location. """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url, base_url, visited):
    """
    Extract all URLs from a given webpage that belong to the same domain.
    """
    urls = set()
    domain_name = urlparse(base_url).netloc

    try:
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
    except:
        return urls # Return empty set on request failure

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        # Resolve relative URLs
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # Clean up the URL
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        # Filter out invalid or previously visited URLs
        if not is_valid_url(href) or href in visited or domain_name not in href:
            continue

        # Add to the set and mark as visited
        urls.add(href)
        visited.add(href)
    return urls

def save_page_data(url, base_path):
    """
    Save the content of a webpage to a file, mirroring the website's directory structure.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse URL and create corresponding file path
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path.endswith('/'):
            path += "index.html"
        else:
            path += '.html'

        # Clean file path
        path = path.replace(':', '_').replace('?', '_').replace('*', '_').replace('"', '_')
        file_path = os.path.join(base_path, parsed_url.netloc, path.lstrip('/'))

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        print(f"Saving to: {file_path}")

        # Write webpage content to file
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(response.text)

    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")

def scrape_website(company_name, website_url, category, format):
    """
    Scrape an entire website and save its content in the specified format.
    """
    visited = set()
    all_urls = get_all_website_links(website_url, website_url, visited)
    base_path = os.path.join("..", "data", "html", company_name)
    new_path = os.path.join("..", "data", format, company_name)

    for url in all_urls:
        save_page_data(url, base_path)

    # Convert HTML to text if required
    if format != "html":
        process_html_2_text(base_path, new_path, company_name, category)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('--format', type=str, help='Scraping format (html/txt)', required=True)
    args = parser.parse_args()

    # Validate format argument
    if args.format not in ["html", "txt"]:
        print("Invalid format. Please use 'html' or 'txt'.")
        sys.exit(1)

    # Read company data from CSV file
    companies_df = pd.read_csv('test_companies.csv', header=None, names=['company', 'website', 'category'])

    # Scrape each company's website
    for index, row in companies_df.iterrows():
        print(f"Scraping {row['company']} website...")
        scrape_website(row['company'], row['website'], row['category'], args.format)

if __name__ == "__main__":
    main()
