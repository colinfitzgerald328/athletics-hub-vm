# Athletics Hub Data Processing and Extraction

## Overview
This codebase contains various Python scripts used for data processing and extraction for the Athletics Hub web application. Athletics Hub is a comprehensive platform designed for track and field enthusiasts to stay connected to the sport throughout the season. The primary purpose of these scripts is to gather and enrich data related to track and field athletes, competitions, and events, and to update the Athletics Hub database with the extracted data on a regular basis.

## Data Retrieval and Processing
The code includes functions and scripts that perform the following tasks:

- **Athlete Data Retrieval:** Queries the World Athletics API and other sources to fetch basic athlete information, such as names, nationalities, and unique identifiers.
- **Athlete Image Retrieval:** Scrapes websites like Google and Getty Images to obtain high-quality images of athletes.
- **Social Media Links Extraction:** Extracts URLs to athletes' social media profiles (Instagram, Twitter, Facebook) from Google search results.
- **Wikipedia URL Retrieval:** Finds the Wikipedia page URL for each athlete by parsing Google search results.
- **Nickname Extraction:** Attempts to extract an athlete's nickname from their Wikipedia page using regular expressions.
- **Instagram Username and Caption Retrieval:** Logs into Instagram using the athlete's username and retrieves the captions from their recent posts for further analysis.
- **High-Quality Image Retrieval:** Retrieves high-quality images of athletes from Getty Images using Google search results.

## Data Enrichment and Analysis
The code also includes functions and scripts for enriching and analyzing the collected data:

- **Calculating Event Scores:** Computes scores for track and field events based on an athlete's time, gender, and event type.
- **Competition ID Retrieval:** Obtains the unique identifier for a competition based on its name and date.
- **Event Results Retrieval:** Scrapes results for a specific event in a track and field competition.


## Database Updates
The code includes scripts for updating the Athletics Hub database with the extracted and processed data:

- **Athlete Document Update:** Updates or inserts a new document in the MongoDB collection for each athlete with the collected information.
- **Top Competitors Retrieval:** Scrapes an athlete's profile page to identify and extract their top competitors' names.
- **Personal Best (PB) Retrieval:** Scrapes the World Athletics website to retrieve an athlete's personal best performances in various events.
- **Accomplishments Retrieval:** Queries the World Athletics API to obtain a list of notable accomplishments for each athlete.

## Automation and Scheduling
The codebase includes scripts that utilize an Amazon EC2 instance to run on a schedule and perform the data extraction and update processes automatically.
