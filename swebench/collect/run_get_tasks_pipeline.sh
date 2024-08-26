#!/usr/bin/env bash

# If you'd like to parallelize, do the following:
# * Create a .env file in this folder
# * Declare GITHUB_TOKENS=token1,token2,token3...

# Read the repos from the file and join them with a comma
REPOS=$(cat ../../repos.txt)

# Run the Python script with the repos
python get_tasks_pipeline.py \
    --repos $REPOS \
    --path_prs 'scrapes/20240701/prs' \
    --path_tasks 'scrapes/20240701/tasks' \
    --cutoff_date '20240701'    
