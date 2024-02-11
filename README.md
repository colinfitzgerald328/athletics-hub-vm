# Athletics Hub VM and Database Management
This repository contains scripts and tools for managing and updating the Athletics Hub database through a virtual machine (VM).
The VM is configured to stream data from WorldAthletics and Wikipedia on intervals and, inserting into the database and performing updates as necessary.
Additionally, there are various scripts included in this repository to summarize data from other sources which are then used on the frontend of the Athletics Hub. 

The core function of this virtual machine is that it is the external architecture which keeps the data on the Athletics Hub up-to-date, in addition to providing a data source (the DB) for the backend server in order to speed API calls and data fetching on the frontned. 

# Features
Database Streaming: The VM is set up to stream data directly into the Athletics Hub database, ensuring that the database is always up-to-date with the latest information.
Automated Updates: Scheduled scripts within the VM automatically perform updates to the database, keeping it synchronized with any changes in the source data.
