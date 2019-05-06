#!/usr/bin/python
import marshal
def load_and_find_min(filepath):
  global min_dist
  global visit_order
  global all_stage_distance_pair
  global tsp
  global tsp_cluster
  global route_stages
  global stages
  with open(filepath + "_distance_from_source.marshal") as f: 
    min_dist = marshal.load(f)
  for k, v in min_dist.iteritems():
    min_distance = 11000000
    print
    print k
    print "--"
    l = len(v) -1
    for s, node in v[l].iteritems():
      if node['distance']['results']['trips'][0]['length'] < min_distance:
        min_distance = node['distance']['results']['trips'][0]['length']
    print min_distance 
  with open(filepath +  "_visit_order.marshal", "rb") as f:
    visit_order = marshal.load(f)
  with open(filepath +  "_all_stage_distance_pair.marshal", "rb") as f:
    all_stage_distance_pair = marshal.load(f)
  with open(filepath +  "_distance_from_source.marshal", "rb") as f:
    tsp = marshal.load( f)
  with open(filepath +  "_tsp_cluster.marshal", "rb") as f:
    tsp_cluster = marshal.load( f)
  with open(filepath +  "_route_stages.marshal", "rb") as f:
    route_stages = marshal.load( f)
  with open(filepath +  "_stages.marshal", "rb") as f:
    stages = marshal.load( f)

