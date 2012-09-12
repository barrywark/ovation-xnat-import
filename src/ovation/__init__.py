'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''


import logging

# Create a console logging handler for ovation package
_log = logging.getLogger(__name__)
_log.addHandler(logging.StreamHandler())
