#!/bin/sh


python convert_bwb.py --all --no-inline-metadata --no-full-graph --rdf-upload-url http://localhost:3020/servlets/uploadData -user admin -pass visstick --skip-if-existing --log-to-file

