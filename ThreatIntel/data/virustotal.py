from __future__ import absolute_import, division, print_function, unicode_literals
import gevent.monkey
#gevent.monkey.patch_socket()
import sys
import getopt
import json
import urllib
import urllib2
import pprint
import requests
from .base import *

class Query:
    def __init__(self,qLoc):
        self.queryLoc=qLoc
        self.resultJSON=dict()
    def setThreat(self,res):
        self.resultJSON['response_code']=res
    def getThreatCode(self):
        if 'resonse_code' in self.resultJSON:
            return self.resultJSON['response_code']
        else:
            return DISP_INDETERMINATE
    def getQueryLoc(self):
        return self.queryLoc
    def setResults(self,data):
        '''Saves the results as a dictionary'''
        self.resultJSON=data
    def getResultData(self):
       return self.resultJSON
    def getResultSummary(self):
        '''This returns important data about the result as a dictionary'''
        results=dict() #Change the names to be more consistent.
        #If we are looking at IPs, we may have to look in a specific key.
        if 'response_code' in self.resultJSON:
            results['response_code']=self.resultJSON['response_code']
        if 'permalink' in self.resultJSON:
            results['permalink']=self.resultJSON['permalink']
        if 'positives' in self.resultJSON:
            results['positives']=self.resultJSON['positives']
        if 'total' in self.resultJSON:
            results['total']=self.resultJSON['total']
        if 'scan_date' in self.resultJSON:
            results['last_event_ts']=self.resultJSON['scan_date']
        if 'url' in self.resultJSON:
            results['scan_url']=self.resultJSON['url']
        return results

#Convert tabs to spaces.
#Make code more readable and look good.
class VirusTotalDataProvider(DataProvider):
    URL_SLOC="https://www.virustotal.com/vtapi/v2/url/report" #Location of URL scan API.
    IP_SLOC="https://www.virustotal.com/vtapi/v2/ip-address/report" #Location of IP scan API.
    SCAN_LOC="" #Location of place that will be scanned.
    TEST_IP="90.156.201.27" #This is a test IP address.

    def __init__(self, apikey):
        self._apikey = apikey

    def scanURL(self,query): 
        '''This method scans a URL and prints the number of positive scans'''
        parameters={"resource":query.getQueryLoc(), "apikey":self._apikey}
        r=requests.post(self.URL_SLOC,parameters) 
        jStr=r.json()     
        if jStr['positives']>2:
            query.setThreat(DISP_POSITIVE)
        elif jStr['positives']==0:
            query.setThreat(DISP_NEGATIVE)
        else:
            query.setThreat(DISP_INDETERMINATE)
            query.setResults(jStr)    

    @property
    def name(self):
        return "virustotal"

    def scanIP(self,query):
        '''This method scans an IP address
           There is currently a socket error here'''
        parameters = {'ip':'173.194.46.67', 'apikey':self._apikey}
        r=requests.post(self.URL_SLOC,parameters)
        try:
            response_dict =r.json()
            if('resolutions' in response_dict)==False: #We are querying an invalid IP address.
                query.setThreat(DISP_INDETERMINATE)
                query.setResults(response_dict)
                return        
            if  ('detected_urls' in response_dict)==False:#Sometimes, data about the scan is not sent.
                query.setThreat(DISP_POSITIVE)
                query.setResults(response_dict)
                return
            sumData=response_dict['detected_urls']
            if sumData['positives']>2: 
                query.setThreat(DISP_POSITIVE)
            elif sumData['positives']==0:
                query.setThreat(DISP_NEGATIVE)
            else:
                query.setThreat(DISP_INDETERMINATE) 
                query.setResults(response_dict)
        except ValueError:
            query.setThreat(DISP_FAILURE) 

    def retrieveReport(query):
        '''This method scans a domain and returns results for that domain'''
        url = 'https://www.virustotal.com/vtapi/v2/domain/report'
        parameters = {'domain': '027.ru', 'apikey':self._apikey}
        r=requests.post(self.URL_SLOC,parameters)
        response_dict =r.json()
        query.setResults(response_dict)
        
    def _query(self,target,qtype):

       aDict={QUERY_URL:self.scanURL,QUERY_IPV4:self.scanIP,QUERY_DOMAIN:self.retrieveReport}      
       while True:
           qLoc=target
           query=Query(qLoc)
           if (qtype in aDict):
               aDict[qtype](query)
           results=InformationSet(query.getThreatCode(),**query.getResultSummary())
           return results
      
   

