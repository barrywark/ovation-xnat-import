'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''


import logging

_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)

# Create a console logging handler for ovation package
console = logging.StreamHandler()
_log.addHandler(console)
