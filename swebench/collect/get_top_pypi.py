#!/usr/bin/env python3

import os
import json
import argparse
import logging
from typing import List, Dict
import pickle

from bs4 import BeautifulSoup
from ghapi.core import GhApi
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

gh_token = os.environ.get("GITHUB_TOKEN")
if not gh_token:
    msg = "Please set the GITHUB_TOKEN environment variable."
    raise ValueError(msg)
api = GhApi(token=gh_token)


def get_package_stats(top_packages, output_file):
    """
    Get package stats from pypi page

    Args:
        top_packages (list): List of packages + HTML
        output_file (str): File to write to
        driver (webdriver): Selenium WebDriver instance
    """
    logger.info(f"Getting package stats for {len(top_packages)} packages")

    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(options=firefox_options)

    # Extra package title, pypi URL, stars, pulls, and github URL
    with open(output_file, "a+") as fp_:
        fp_.seek(0)  # Move the file pointer to the beginning
        content = fp_.read()

        for i, package in enumerate(top_packages, 1):
            logger.debug(f"Processing package {i}/{len(top_packages)}: {package}")
            # Get package name and pypi URL
            package_name = package["title"]
            package_url = package["href"]
            if package_url in content:
                continue

            # Get github URL
            package_github = None
            driver.get(package_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            for link in soup.find_all("a", class_="vertical-tabs__tab--with-icon"):
                found = False
                for x in ["Source", "Code", "Homepage"]:
                    if (
                        x.lower() in link.get_text().lower()
                        and "github" in link["href"].lower()
                    ):
                        package_github = link["href"]
                        found = True
                        break
                if found:
                    break

            # Get stars and pulls from github API
            stars_count, pulls_count = None, None
            if package_github is not None:
                repo_parts = package_github.split("/")[-2:]
                owner, name = repo_parts[0], repo_parts[1]

                try:
                    repo = api.repos.get(owner, name)
                    stars_count = int(repo["stargazers_count"])
                    issues = api.issues.list_for_repo(owner, name)
                    pulls_count = int(issues[0]["number"])
                except:
                    pass

            # Write to file
            logger.debug(f"Writing data for {package_name}")
            print(
                json.dumps(
                    {
                        "rank": i,
                        "name": package_name,
                        "url": package_url,
                        "github": package_github,
                        "stars": stars_count,
                        "pulls": pulls_count,
                    }
                ),
                file=fp_,
                flush=True,
            )

    logger.info(f"Finished processing all packages. Data written to {output_file}")


def get_top_pypi_packages(max_repos: int) -> List[Dict[str, str]]:
    """
    Get top PyPI packages from hugovk's page.

    Args:
        max_repos (int): Maximum number of repos to get

    Returns:
        List[Dict[str, str]]: List of dictionaries containing package info
    """
    logger.info(f"Fetching top {max_repos} PyPI packages")

    # Set up Firefox in headless mode
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(options=firefox_options)

    try:
        # Start selenium driver to get top PyPI packages
        url_top_pypi = "https://hugovk.github.io/top-pypi-packages/"
        logger.debug(f"Accessing URL: {url_top_pypi}")
        driver.get(url_top_pypi)

        logger.debug("Clicking 'Show more' button")
        button = driver.find_element(By.CSS_SELECTOR, 'button[ng-click="show(8000)"]')
        button.click()

        # Retrieve HTML for packages from page
        logger.debug("Parsing page content")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        package_list = soup.find("div", {"class": "list"})
        packages = package_list.find_all("a", class_="ng-scope")

        result = [
            {"title": pkg["title"], "href": pkg["href"]} for pkg in packages[:max_repos]
        ]
        logger.info(f"Successfully fetched {len(result)} packages")
        return result
    except Exception as e:
        logger.error(f"Error fetching top PyPI packages: {str(e)}")
        raise
    finally:
        logger.debug("Closing Selenium driver")
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-repos", help="Maximum number of repos to get", type=int, default=5000
    )
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    parser.add_argument(
        "--force-fetch", help="Force fetching packages from web", action="store_true"
    )
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info(f"Starting script with max_repos={args.max_repos}")

    cache_file = "top_packages_cache.pkl"

    if not args.force_fetch and os.path.exists(cache_file):
        logger.info("Reading top packages from cache")
        with open(cache_file, "rb") as f:
            top_packages = pickle.load(f)
    else:
        logger.info("Fetching top packages from web")
        top_packages = get_top_pypi_packages(args.max_repos)
        with open(cache_file, "wb") as f:
            pickle.dump(top_packages, f)

    get_package_stats(top_packages, "pypi_rankings.jsonl")
    logger.info("Script completed successfully")
