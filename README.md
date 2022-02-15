# Reveal

A bokeh application for analyzing your transactions from Tinkoff bank account report

## Requirements
Docker, docker-compose, browser, git-lfs

## Installation
Run as dev
```
docker-compose -f docker/compose-dev.yaml up -d && docker-compose -f docker/compose-dev.yaml exec reveal_dev bash
```
Run as prod
```
docker-compose -f docker/compose-prod.yaml up
```

## Usage

Run the app (see above). Find the url of the app (probably it would be http://localhost:5006/src).
Upload your tinkoff bank account report as .xls file.
Behold all the money you wasted for good.
