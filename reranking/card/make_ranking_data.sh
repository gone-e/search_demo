#!/bin/bash

Service="card"
Featureset="card.test.v1"
Goldenset="./dataset/card/ranking/test.txt"
Dumppath="./reranking/card/test.add.txt"

echo "python reranking/make_ranking_data.py --service=${Service} --featureset=${Featureset} --goldenset=${Goldenset} --dumppath=${Dumppath}"
python reranking/make_ranking_data.py --service=${Service} --featureset=${Featureset} --goldenset=${Goldenset} --dumppath=${Dumppath}
