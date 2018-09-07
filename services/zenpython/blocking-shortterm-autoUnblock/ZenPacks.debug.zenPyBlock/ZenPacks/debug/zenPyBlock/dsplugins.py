# Logging
import logging
LOG = logging.getLogger('zen.zenPyBlock')

# stdlib Imports
from time import sleep
from random import random

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
#from twisted.internet import utils
from twisted.web.client import getPage


# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )
from Products.DataCollector.plugins.DataMaps import ObjectMap

# Zenpack provided lib imports

# Set GLOBAL variables

class zenPyBlock(PythonDataSourcePlugin):
   """zenPyBlock stats data source plugin."""

   # List of device attributes you'll need to do collection.
   proxy_attributes = (
      'zStatusConnectTimeout'
   )

   @classmethod
   def config_key(cls, datasource, context):
      return (
         context.device().id,
         datasource.getCycleTime(context),
         'zenPyBlock',
      )

   @classmethod
   def params(cls, datasource, context):
      return {
         'zStatusConnectTimeout': context.zStatusConnectTimeout,
      }

   @inlineCallbacks
   def collect(self, config):
      data = self.new_data()
      
      #Set Variables
      for datasource in config.datasources:
         #Collect/Update DataPoints
         yield sleep(0.1)
         sleep(datasource.params['zStatusConnectTimeout'])
         ##Steve: datasource description 'should' match one of the headers returned from haproxy stats page
         for datapoint_id in (x.id for x in datasource.points):
            #store datapoints
            dpname = '_'.join((datasource.datasource, datapoint_id))
            data['values'][datasource.component][dpname] = (random(), 'N')
            
      returnValue(data)
