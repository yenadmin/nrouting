#!/usr/bin/python

import argparse
import csv
import json
import math
import pandas as pd
import requests
import sys
import urllib
import urlparse

OAUTH_URL = "https://outpost.mapmyindia.com/api/security/oauth/token?"
MAP_API_ENDPOINT = "https://apis.mapmyindia.com/advancedmaps/v1/"
LICENCE_KEY="zqefn3w1jkgvuzkv4pzmiyyt1nt23872"
MAXIMUM_METERS  = 10000000 # Assuming our travel distance would never cross 1000 KMS
EARTH_RADIUS = 6371000 # meaters
ZERO = 0.0000001
ROUTE_BY_GOOGLE = False 
GOOGLE_MAPS_KEY = 'AIzaSyC5ltlEtUqZmGo6uC5gAl5EUgNnu5zjp5A'

def radians(deg):
  return deg * math.pi / 180.0

def haversine_distance(lat1, lon1, lat2, lon2):
  ph1 = radians(lat1)
  ph2 = radians(lat2)
  dph = radians(lat2 - lat1)
  dlm = radians(lon2 - lon1)
  a = (math.sin(dph / 2) * math.sin(dph / 2) + 
      math.cos(ph1 / 2) * math.cos(ph2 / 3) *
      math.sin(dlm / 2) * math.sin(dlm / 2))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
  d = EARTH_RADIUS * c
  return d

def euclidean_distance(lat1, lon1, lat2, lon2):
  m1 = lat2 - lat1
  m2 = lon2 - lon1
  dsq = m1 * m1 + m2 * m2 
  return math.sqrt(dsq)
  
def manhattan_distance(lat1, lon1, lat2, lon2):
  m1 = lat2 - lat1
  m2 = lon2 - lon1
  return abs(m1) + abs(m2) 
  
def euclidian_slope(lat1, lon1, lat2, lon2):
  m1 = lat2 - lat1
  m2 = lon2 - lon1
  if abs(m2) <= ZERO:
    return math.pi / 2
  return math.atan(m1/m2)

def euclidian_perpendicular_distance(lat1, lon1, lat2, lon2, lat3, lon3):
  m1 = lat2 - lat1
  m2 = lon2 - lon1
  if abs(m1) <= ZERO and  abs(m2) <= ZERO :
    print "Error"
    return -1
  dn = m2 * lat3 - m1 * lon3 + lat2 * lon1 - lat1 * lat2
  return abs(dn) / math.sqrt(m1 * m1 + m2 * m2)


def get_ratio(lat1, lon1, lat2, lon2, lat0, lon0):
  dex = lat0 - lat2  
  nux = lat1 - lat0
  if abs(dex) < ZERO:
    print "Error"
    return 0  
  ratio = nux * 1.0 / dex

def intersecting_ratio_by_perpanducular_from(lat1, lon1, lat2, lon2, lat0, lon0):
  mx = lat2 - lat1
  my = lon2 - lon1
  mx1 = lat1 - lat0
  my1 = lon1 - lon0
  mx2 = lat2 - lat0
  my2 = lon2 - lon0
  de = mx * mx2 + my * my2
  nu = mx * mx1 + my * mx1
  if abs(de) <= ZERO:
    # TODO fix 
    print "Error"
    return 0
  return -1.0 * nu / de
  
def ratio_point(lat1, lon1, lat2, lon2, m, n):
  de = (m + n) * 1.0
  if abs(de) < ZERO:
    print "Error"
    return 0
  nx = lat1 * m + lat2 * n 
  ny = lon1 * m + lon2 * n
  return (nx / de, ny / de) 

def get_config(config, sep='\t'):
  with open(config) as f:
    lines = f.readlines()
  conf = {}
  for entry in lines:
    k_v = entry.split(sep)
    conf[k_v[0]] = k_v[1].strip()
  return conf

def get_auth_token(credentials):
  params = get_config(credentials)
  headers =  {'Content-Type' : 'application/x-www-form-urlencoded'}
  json_response = requests.post(OAUTH_URL,
                                params=params,
                                headers=headers)
  print params
  if json_response.status_code not in [200]:
    print "Errpr in authorizations", json_response.status_code, json_response.json()
    sys.exit(1)
  return json_response.json()


def get_lat_lon_from_short_uri(suri):
  headers =  {} #{'Content-Type' : 'application/x-www-form-urlencoded'}
  url = "https://www.googleapis.com/urlshortener/v1/url?" 
  geourl = "https://maps.googleapis.com/maps/api/geocode/json?"
  params = { 'shortUrl' : suri,
             'key' : 'AIzaSyCPzFQxhmB_eauqMHIzmU7BkLTOPb89bqU'
              }
  json_response = requests.get(url, params=params, headers=headers)
  lurl = json_response.json().get('longUrl', "Error")
  if lurl.startswith('https://maps.app.goo.gl/?link='):
    lurl = lurl[len('https://maps.app.goo.gl/?link='):]
  uqurl = urllib.unquote(lurl) # .decode('utf8')
  if uqurl.startswith('https://www.google.com/maps/place/'):
    urlquery = urllib.splitquery(uqurl)[0]
    if urlquery.find('/data'):
      data = urlquery.split('/data')[1].split('!')
      lat, lon = data[-2][2:], data[-1][2:].split('?')[0]
      if lat != '1':
        return lat, lon 
  elif uqurl.startswith('https://maps.google.com/?q='):
    urlquery = urllib.splitquery(uqurl)
    urlparams = urlparse.parse_qs(urlquery[1])['q'][0]
    params['address'] = urlparams
    del params['shortUrl']
    json_result = requests.get(geourl, params=params, headers=headers).json()
    location = json_result["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]
  print "lurl needs more analysis", lurl
  return 'FIX_LAT', 'FIX_LON'


#a = combine_lat_lon_customers('/Users/arulsmv/Downloads/tmp/cust-list-orig.tsv')
#write_geocoded_address_to_file('/Users/arulsmv/Downloads/tmp/cust-list.tsv', a)

def combine_lat_lon_customers(tsv_file):
  geocoded_customers = [] 
  with open(tsv_file) as tfile:
    csvr = csv.DictReader(tfile, delimiter='\t')
    for cust in csvr:
      customer = {}
      print cust['S.No.'], 
      customer['Customer Name'] = cust['Customer Name']
      customer['address'] = cust['Address']
      customer['Cust ID'] = cust['S.No.']
      if cust.get('Google Map Link') != None or len(cust.get('Google Map Link').strip()) > 0:
        lat, lon = get_lat_lon_from_short_uri(cust['Google Map Link'])
        customer['latitude'] = lat
        customer['longitude'] = lon
      else:
        customer['latitude'] = 'FIX_LAT' 
        customer['longitude'] = 'FIX-LON'
      geocoded_customers.append(customer)
      print
  return geocoded_customers 


def read_customers(tsv_file, token):
  geocoded_customers = [] 
  with open(tsv_file) as tfile:
    csvr = csv.DictReader(tfile, delimiter='\t')
    for cust in csvr:
      geocoded = populate_geocode(cust, token)
      geocoded_customers.append(geocoded)
  return geocoded_customers 

def get_geocode(address, token):
  URL = "https://atlas.mapmyindia.com/api/places/geocode?";
  params = {"access_token" : token['access_token'], "address" : address}
  headers =  {'Content-Type' : 'application/x-www-form-urlencoded'}
  json_response = requests.get(URL, params=params, headers=headers)
  return json_response.json()

def populate_geocode(cust, token):
  customer = {}
  geocode = get_geocode(cust['Address'], token)
  customer['latitude'] = geocode[u'copResults']['latitude']
  customer['longitude'] = geocode [u'copResults']['longitude']
  customer['Customer Name'] = cust['Customer Name']
  customer['address'] = cust['Address']
  customer['Cust Id'] = cust['S.No.']
  return customer 
  
def get_driections(location1, location2):
  start = "%f,%f" % (location1['latitude'], location1['longitude'])
  destination ="%f,%f" % (location2['latitude'], location2['longitude'])
  if ROUTE_BY_GOOGLE == True:
     return get_direction_from_google(start, destination)
  return get_direction_from_mapmyindia(start, destination)

def get_direction_from_google(start, destination):
  url = 'https://maps.googleapis.com/maps/api/directions/json?'
  params = { 
    'key': GOOGLE_MAPS_KEY,
     'origin': start,
     'destination': destination
  }
  headers =  {} #{'Content-Type' : 'application/x-www-form-urlencoded'}
  json_response = requests.get(url,
                               params=params,
                               headers=headers)
  return json_response.json()[u'routes'][0]['legs'][0]['distance']['value']

def get_direction_from_mapmyindia(start, destination):
  service="/route"
  # distance_between="%f,%f;%f,%f" % (location1['latitude'], location1['longitude'], location2['latitude'], location2['longitude'])
  headers =  {} #{'Content-Type' : 'application/x-www-form-urlencoded'}
  params = { 
            'rtypee': 1, 
            'region' : 'ind',
            'start' : start,
            'destination' : destination
           }
  print params
  url = MAP_API_ENDPOINT + LICENCE_KEY + service 
  json_response = requests.get(url,
                               params=params,
                               headers=headers)
  return json_response.json()[u'results'][u'trips'][0][u'length']


def find_distances_metrix(cusotmers):
  distance = {}
  size = len(cusotmers)
  for i in range(size):
    distance[i] = {}
    for j in range(size):
      if (i == j):  continue
      distance[i][j] = get_driections(cusotmers.iloc[i], cusotmers.iloc[j])
  return distance

  
def write_geocoded_address_to_file(output, geocoded):
  with open(output, 'w+') as outf:
    writer = csv.DictWriter(outf, geocoded[0].keys(), delimiter="\t")
    writer.writeheader()
    for row in geocoded:
      writer.writerow(row)



def main():
  parser = argparse.ArgumentParser(description="Process some integers.")
  parser.add_argument('--credentials', default="/Users/arulsmv/.mapmyindia.credentials")
  parser.add_argument('--customers', default="/Users/arulsmv/yen/nconnect/mapmyinida/data/customer_list.csv")
  parser.add_argument('--output', default="/tmp/geocoded.tsv")

  args = parser.parse_args()
  token = get_auth_token(args.credentials)
  geo_coded_customers = read_customers(args.customers, token)
  write_geocoded_address_to_file(args.output, geo_coded_customers)

if __name__ == '__main__':
  main()
