#!/bin/bash

echo "Downloading Chinook database..."
wget https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql

echo "Creating database..."
sqlite3 Chinook.db < Chinook_Sqlite.sql

echo "Done"