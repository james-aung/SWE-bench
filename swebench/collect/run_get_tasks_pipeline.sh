#!/usr/bin/env bash

# If you'd like to parallelize, do the following:
# * Create a .env file in this folder
# * Declare GITHUB_TOKENS=token1,token2,token3...

python get_tasks_pipeline.py \
    --repos 'astropy/astropy', 'django/django', 'matplotlib/matplotlib', \
            'mwaskom/seaborn', 'pallets/flask', 'psf/requests', \
            'pydata/xarray', 'pylint-dev/pylint', 'pytest-dev/pytest', \
            'scikit-learn/scikit-learn', 'sphinx-doc/sphinx', 'sympy/sympy' \
    --path_prs 'scrapes/20231101/prs' \
    --path_tasks 'scrapes/20231101/tasks' \
    --cutoff_date '20231101'