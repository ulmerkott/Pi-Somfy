#!/bin/sh
pigpiod -m
python ./operateShutters.py -auto -mqtt