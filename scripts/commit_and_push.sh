#!/bin/bash

git add .
git commit -m 'temporary'
git push origin master

cd ../myelasticsearch
git add .
git commit -m 'temporary'
git push origin master
