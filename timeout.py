#!/bin/env python

from threading import Timer

def huge_computation(self, input):
    sleep(1)
    return input.upper()

def execute(function, timeout=0):
    output = None
    if timeout == 0:
        output = function()
    else
        

