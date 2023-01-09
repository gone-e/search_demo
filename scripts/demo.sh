#!/bin/bash

# You can also pass a URL to streamlit run! This is great when combined with Github Gists. For example:
# $ streamlit run https://raw.githubusercontent.com/streamlit/demo-uber-nyc-pickups/master/streamlit_app.py

# echo "streamlit run streamlit_app.py"
# streamlit run streamlit_app.py

# echo "streamlit config show"
# streamlit config show

# https://docs.streamlit.io/knowledge-base/using-streamlit/streamlit-watch-changes-other-modules-importing-app
export PYTHONPATH=$PYTHONPATH:`pwd`
#export PYTHONPATH=$PYTHONPATH:$(dirname "$(realpath $0)")

DemoDir="./demo/"
cd ${DemoDir}
AppFile="streamlit_app.py"
Port="30060"
BaseUrlPath="demo"


#streamlit run ${AppFile} --server.port ${Port} --server.baseUrlPath ${BaseUrlPath}
streamlit run ${AppFile} --server.port ${Port}
