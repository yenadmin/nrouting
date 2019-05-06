#!/usr/bin/python

from generate_cluster import COLOURS
from generate_cluster import MARKERS

import json

# Adssumes groups are manually entered pairs of (colour, marker) list per group except the last.

def grouping(groups, cluster_size):
  routes = []
  identified_cluster=set()
  for i in range(len(groups)):
    clusterset = set()
    for c, m in groups[i]:
      index = COLOURS.index(c) * len(COLOURS) + MARKERS.index(m)
      clusterset.add(index)
      identified_cluster.add(index)
    routes.append(list(clusterset))
  universal = set(range(cluster_size))
  finalset = universal.difference(identified_cluster)
  routes.append(list(finalset))
  return routes

def main():
  route_count = input("Enter total routes : ")
  total_clusters = input("Enter clusters count : ")
  route_groups = {} 
  for i in range(route_count - 1):
    route_groups[i] = []
    while True:
      print "Grouping for route " + str(i) 
      c = raw_input("Enter colour : ")
      m = raw_input("Enter marker : ")
      route_groups[i].append((c, m))
      y = raw_input("Add more to route " + str(i))
      if y != 'y' and y != 'Y':
        print "Moving to next group"
        break
  routes = grouping(route_groups, total_clusters) 
  print routes
  with open("/tmp/groupped.txt", "w") as f:
    line = json.dumps(routes)
    f.write(line)
      

if __name__ == '__main__':
  main()
