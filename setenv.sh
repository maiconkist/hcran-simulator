#!/bin/sh

export THONPATH=~/git-reps/simulations/lib/:~/git-reps/simulations/submodules/pymobility/src/

# To set the cscope to python
find . -name '*.py' > cscope.files
cscope -pkR


