#!/usr/bin/env python3

import os, json
import argparse

from bs4 import BeautifulSoup
from ghapi.core import GhApi
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By


gh_token = os.environ.get("GITHUB_TOKEN")
if not gh_token:
    msg = "Please set the GITHUB_TOKEN environment variable."
    raise ValueError(msg)
api = GhApi(token=gh_token)


def get_package_stats(data_tasks, f):
    """
    Get package stats from pypi page

    Args:
        data_tasks (list): List of packages + HTML
        f (str): File to write to
    """
    # Adjust access type if file already exists
    content = None
    access_type = "w"
    if os.path.exists(f):
        with open(f) as fp_:
            content = fp_.read()
            access_type = "a"
            fp_.close()

    # Extra package title, pypi URL, stars, pulls, and github URL
    with open(f, access_type) as fp_:
        for idx, chunk in enumerate(data_tasks):
            # Get package name and pypi URL
            package_name = chunk["title"]
            package_url = chunk["href"]
            if content is not None and package_url in content:
                continue

            # Get github URL
            package_github = None
            driver.get(package_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # First attempt: look for specific links
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

            # Second attempt: look for GitHub statistics in sidebar
            if not package_github:
                github_stats = soup.find("div", class_="github-repo-info")
                if github_stats:
                    links = github_stats.find_all("a", class_="vertical-tabs__tab")
                    for link in links:
                        href = link.get("href", "")
                        if any(
                            x in href
                            for x in [
                                "stargazers",
                                "network/members",
                                "issues",
                                "pulls",
                            ]
                        ):
                            package_github = "/".join(
                                href.split("/")[:5]
                            )  # Get base GitHub URL
                            break

            # Get stars and closed PRs from github API
            stars_count, closed_prs_count = None, None
            if package_github is not None:
                repo_parts = package_github.split("/")[-2:]
                owner, name = repo_parts[0], repo_parts[1]

                try:
                    repo = api.repos.get(owner, name)
                    stars_count = int(repo["stargazers_count"])

                    # Get closed PRs
                    closed_prs = api.pulls.list(owner, name, state="closed", per_page=1)
                    closed_prs_count = closed_prs.total_count

                except Exception as e:
                    print(f"Error fetching data for {owner}/{name}: {str(e)}")
                    stars_count, closed_prs_count = None, None

            # Write to file
            print(
                json.dumps(
                    {
                        "rank": idx,
                        "name": package_name,
                        "url": package_url,
                        "github": package_github,
                        "stars": stars_count,
                        "closed_prs": closed_prs_count,
                    }
                ),
                file=fp_,
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-repos", help="Maximum number of repos to get", type=int, default=5000
    )
    args = parser.parse_args()

    # Set up Firefox in headless mode
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(options=firefox_options)

    # Start selenium driver to get top pypi page
    url_top_pypi = "https://hugovk.github.io/top-pypi-packages/"
    driver.get(url_top_pypi)
    button = driver.find_element(By.CSS_SELECTOR, 'button[ng-click="show(8000)"]')
    button.click()

    # Retrieve HTML for packages from page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    package_list = soup.find("div", {"class": "list"})
    packages = package_list.find_all("a", class_="ng-scope")

    get_package_stats(packages[: args.max_repos], "pypi_rankings.jsonl")
