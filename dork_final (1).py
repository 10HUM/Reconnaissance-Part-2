"""
README
======
Automated Google Dorking Script

Purpose:
    This script automates Google dorking for reconnaissance purposes. It
    generates predefined Google dork queries to identify:
        - Exposed login pages (inurl:login)
        - Publicly accessible documents (filetype:pdf OR filetype:doc)
        - Open/exposed databases (intitle:index.of mysql)

Functionality:
    - generate_dork_queries(): Returns a list of predefined dork queries.
    - send_search_request(query): Sends a GET request to Google Search for
      a given query, with error handling for failed/blocked requests.
    - parse_search_results(html): Parses the returned HTML with
      BeautifulSoup and extracts URLs found in <a> tags.
    - perform_dorking(): Runs the full dorking workflow. Uses user-supplied
      queries if set via set_custom_queries(), otherwise falls back to the
      predefined queries. Skips queries already completed (resume feature)
      and saves progress after each query.
    - save_results(results): Appends/saves results to dorking_results.txt.
    - load_completed_queries(): Reads dorking_results.txt (if present) to
      determine which queries have already been processed, enabling the
      script to resume an interrupted run instead of repeating requests.
    - main(): Ties everything together - prompts the user for optional
      custom queries, runs perform_dorking(), and saves results.

Usage:
    Run the script directly:
        python dork_final.py
    When prompted, either press Enter to use the default dork queries, or
    type comma-separated custom queries to search for instead.

Notes:
    - A 2 second delay is added between requests to reduce the risk of
      being rate-limited or blocked by Google.
    - Google actively blocks automated scraping; this script is intended
      for educational purposes within a controlled lab environment.
"""

import requests
from bs4 import BeautifulSoup
import time
import os

# Define user-agent to mimic a real browser
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

# Base Google search URL
GOOGLE_SEARCH_URL = "https://www.google.com/search?q="

RESULTS_FILE = "dorking_results.txt"

# Holds user-supplied queries (populated via set_custom_queries()).
# perform_dorking() checks this list; if empty, it falls back to the
# predefined queries from generate_dork_queries(). This lets
# perform_dorking() accept user-input queries while keeping its
# signature as def perform_dorking():
CUSTOM_QUERIES = []


def set_custom_queries(queries):
    """Set user-supplied dork queries to be used by perform_dorking()."""
    global CUSTOM_QUERIES
    CUSTOM_QUERIES = queries


# Step 2: Add functions here
def generate_dork_queries():
    """Generate Google dorking queries for security research."""
    queries = [
        "inurl:login",  # Find login pages
        "filetype:pdf OR filetype:doc",  # Find exposed documents
        "intitle:index.of mysql"  # Find open databases
    ]
    return queries


def send_search_request(query):
    """Send a request to Google Search."""
    try:
        search_url = GOOGLE_SEARCH_URL + query
        response = requests.get(search_url, headers=HEADERS)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: Unable to fetch results for {query}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def parse_search_results(html):
    """Extract search result URLs from Google's search response."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for link in soup.find_all('a'):
        href = link.get('href')
        if href and "http" in href:
            results.append(href)

    return results


# Step 3: Integrate Google search requests here
def load_completed_queries():
    """Read the results file (if it exists) to determine which queries
    have already been searched, so a search can be resumed."""
    completed = set()

    if not os.path.exists(RESULTS_FILE):
        return completed

    try:
        with open(RESULTS_FILE, "r") as file:
            for line in file:
                if line.startswith("Results for: "):
                    completed.add(line.replace("Results for: ", "").strip())
    except (IOError, OSError) as e:
        print(f"Warning: Could not read existing results file: {e}")

    return completed


def perform_dorking():
    """Perform Google dorking using predefined queries, or user-supplied
    queries if any have been provided via set_custom_queries().

    Supports resuming: queries already present in the results file are
    skipped so the search is not repeated unnecessarily.
    """
    queries = CUSTOM_QUERIES if CUSTOM_QUERIES else generate_dork_queries()

    completed_queries = load_completed_queries()
    all_results = {}

    for query in queries:
        if query in completed_queries:
            print(f"Skipping already completed query: {query}")
            continue

        print(f"Searching: {query}")

        try:
            html = send_search_request(query)

            if html:
                results = parse_search_results(html)
                all_results[query] = results
                # Save progress after each query so results are not lost
                # and the script can resume if interrupted.
                save_results({query: results}, append=True)
            else:
                print(f"No results retrieved for: {query}")

            time.sleep(2)  # Prevent rapid requests to Google

        except Exception as e:
            print(f"Unexpected error while processing '{query}': {e}")
            continue

    return all_results


# Step 4: Process and store search results here
def save_results(results, append=False):
    """Save search results to a text file.

    If append is True, results are appended to the existing file
    (used to support resuming searches). Otherwise the file is
    overwritten.
    """
    mode = "a" if append else "w"

    try:
        with open(RESULTS_FILE, mode) as file:
            for query, urls in results.items():
                file.write(f"Results for: {query}\n")
                for url in urls:
                    file.write(f"{url}\n")
                file.write("\n")

        print(f"Results saved to {RESULTS_FILE}")

    except (IOError, OSError) as e:
        print(f"Error: Could not save results: {e}")


# Main execution function
def main():
    print("Welcome to the Automated Google Dorking Script!")

    # Step 5: Call functions and execute script logic here
    try:
        user_input = input(
            "Enter custom dork queries separated by commas, "
            "or press Enter to use the default queries: "
        ).strip()

        if user_input:
            queries = [q.strip() for q in user_input.split(",") if q.strip()]
            set_custom_queries(queries)

        results = perform_dorking()

        if results:
            print("Dorking complete. Final summary saved to file.")
        else:
            print("No new results were retrieved (all queries may already be completed).")

    except KeyboardInterrupt:
        print("\nScript interrupted by user. Progress has been saved and can be resumed later.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
