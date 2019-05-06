#!/usr/bin/python

from sklearn import datasets
from sklearn.cluster import KMeans

import argparse
import csv
import json
import marshal
import pandas as pd
import matplotlib.pyplot as plt
import get_geocodes
import permutations

def compute_all_pair_centroid_metric(centroid_points):
  all_pair_centroid_metric = {}
  for i in range(len(centroid_points)):
    all_pair_centroid_metric[i] = {}
    src = centroid_points[i]
    for j in range(len(centroid_points)):
      dst = centroid_points[j]
      if i == j: continue
      all_pair_centroid_metric[i][j] ={}
      h_distance = get_geocodes.haversine_distance(src[0], src[1], dst[0], dst[1])
      e_distance = get_geocodes.euclidean_distance(src[0], src[1], dst[0], dst[1])
      e_slope_in_rad = get_geocodes.euclidian_slope(src[0], src[1], dst[0], dst[1])
      all_pair_centroid_metric[i][j]['h_distance'] = h_distance
      all_pair_centroid_metric[i][j]['e_distance'] = e_distance  
      all_pair_centroid_metric[i][j]['e_slope_in_rad'] = e_slope_in_rad  
      all_pair_centroid_metric[i][j]['is_north'] = dst[0] > src[0]
      all_pair_centroid_metric[i][j]['is_east'] = dst[1] > src[1]
  return all_pair_centroid_metric

def compute_groups(all_pair_centroid_metric, num_routes):
  mdfs=pd.DataFrame(columns = ['e_slope_in_rad', 'is_east', 'is_north'],   
                        data = [[x['e_slope_in_rad'], x['is_east'], x['is_north']] for x in all_pair_centroid_metric[0].values()] )
  ckms = KMeans(n_clusters = num_routes).fit(mdfs)
  grouping = {}
  for i in range(len(ckms.labels_)):
    group = grouping.get(ckms.labels_[i], [])
    group.append(i)
    grouping[ckms.labels_[i]] = group
  return grouping
     

# for every cluster identified find the shortest traveling salse man path for evey pair in the cluster nodes.
def all_pair_tsp(stages):
  tsp ={}
  for index, metrics in stages.iteritems():
    tsp[index] = {}
    distance_metrics = metrics['distance']
    permutation_size = len(distance_metrics) 
    if (permutation_size > 2 ):
      for source in range(permutation_size):
        tsp[index][source] = {}
        for destination in range(permutation_size):
           tsp[index][source][destination] = { "distance" : get_geocodes.MAXIMUM_METERS, "rank" : -1 } # rough big number
      for rank in range(permutations.nPr(permutation_size, permutation_size)):
        permutation = permutations.ranked_permutation(rank, permutation_size, permutation_size)
        source = permutation[0]
        destination = permutation[permutation_size - 1]
        curr = source
        permutation.remove(source)
        distance = 0
        for nextpoint in permutation:
          distance += distance_metrics[curr][nextpoint]
          curr = nextpoint
        if (tsp[index][source][destination]["distance"] > distance):
          tsp[index][source][destination]["distance"] = distance
          tsp[index][source][destination]["rank"] = rank
    elif permutation_size == 2:
      tsp[index][0] = {}
      tsp[index][1] = {}
      tsp[index][0][1] = {"distance" : distance_metrics[0][1], "rank" : 0}
      tsp[index][1][0] = {"distance" : distance_metrics[1][0], "rank" : 1}
    else: 
      print "skipping single node cluster" 
  return tsp



def compute_distance_metrics(clusters):
  stages = {}
  for index, customers in clusters.iteritems():
    stages[index] = {}
    stages[index]["distance"] = get_geocodes.find_distances_metrix(customers)
  return stages

# Creates the data frame with centroids that was defined for given route. 
def centroids_group_df(groups, kmeans, hub_lat_lon=[13.023858, 80.163588]):
  centroids = {}
  for index in range(len(groups)):
    centroid = [hub_lat_lon]
    for elem in groups[index]:
      centroid.append(kmeans.cluster_centers_[elem].tolist())
    centroids[index] = pd.DataFrame(columns=['latitude', 'longitude'], data=centroid)
  return centroids

def find_min_path(centroid_paths):
  path ={}
  for stage, tsps in centroid_paths.iteritems():
    minimum = get_geocodes.MAXIMUM_METERS
    rank = -1
    for value in tsps[0].values():
      if value['distance'] < minimum:
         minimum = value['distance']
         rank = value['rank']
    path[stage] = (minimum, rank)
  return path

def find_visit_order(route, grouped):
  visit_order = {}
  for route_num, (d,r) in route.iteritems():
    size = len(grouped[route_num]) + 1 # including origin
    pat = permutations.ranked_permutation(r, size, size)
    pat.remove(0)
    order = []
    for center in pat:
      order.append(grouped[route_num][center - 1])
    visit_order[route_num] = order 
  return visit_order


def find_pair_wise_distance_between(from_stage, to_stage,  clusters):
  pair_wise_distance = {}
  for from_node in range(len(clusters[from_stage])):
    pair_wise_distance[from_node] = {}
    for to_node in range(len(clusters[to_stage])):
      distance = get_geocodes.get_driections(clusters[from_stage].iloc[from_node], clusters[to_stage].iloc[to_node])
      pair_wise_distance[from_node][to_node] = distance
  return pair_wise_distance


def find_pair_wise_distance_for_cluster(visit_order,  clusters):
  all_stage_distance_pair = {}
  for route_num, route_path in visit_order.iteritems():
    all_stage_distance_pair[route_num] = {}
    for stage in range(len(route_path) -1):
      all_stage_distance_pair[route_num][stage] = find_pair_wise_distance_between(route_path[stage], route_path[stage + 1], clusters)
  return all_stage_distance_pair
 
def find_distance_from_sourcee(clusters, visit_order, hub_lat_lon=[13.023858, 80.163588]):
  starting = {'latitude' : hub_lat_lon[0], 'longitude' : hub_lat_lon[1]}
  distance_from_source = {}
  for route_num, route_path in visit_order.iteritems():
    first_cluster = route_path[0]
    distance_from_source[route_num] = {}
    distance_from_source[route_num][0] = {}
    for node_index in range(len(clusters[first_cluster])):
      dis = get_geocodes.get_driections(starting, clusters[first_cluster].iloc[node_index])
      node_id = clusters[first_cluster].iloc[node_index].name
      distance_from_source[route_num][0][node_index] = {'distance' : dis, 'node_details': {'first_node' : node_id}}
  return distance_from_source
  

def find_minimal_path_for_route(all_stage_distance_pair, clusters, tsp, visit_order, distance_from_source, hub_lat_lon=[13.023858, 80.163588]):
  for route_num, route_path in visit_order.iteritems():
    for stage_id in range(len(route_path) - 1):
      cluster_source_nodes = clusters[route_path[stage_id]]
      cluster_destination_nodes = clusters[route_path[stage_id + 1]]
      stage_distance_pair = all_stage_distance_pair[route_num][stage_id]
      distance_from_source[route_num][stage_id + 1] = {}
      for destination_index in range(len(cluster_destination_nodes)):
        # TODO: Change the formating.
        distance_from_source[route_num][stage_id + 1][destination_index] = {'distance' : get_geocodes.MAXIMUM_METERS, 'node_details': {}} 
      for source_index in range(len(cluster_source_nodes)):
        d0 = distance_from_source[route_num][stage_id][source_index]['distance']
        for exit_node_index in range(len(cluster_source_nodes)):
          if source_index == exit_node_index: 
            if len(cluster_source_nodes) == 1: d1 =0
            else: continue
          else:
            print stage_id,  route_path[stage_id], source_index, exit_node_index
            d1 = tsp[route_path[stage_id]][source_index][exit_node_index]['distance']
          for entry_node_index in range(len(cluster_destination_nodes)):
            d2 = stage_distance_pair[exit_node_index][entry_node_index]
            for destination_index in range(len(cluster_destination_nodes)):
              if entry_node_index == destination_index: 
                if len(cluster_destination_nodes) == 1: d3 =0
                else: continue
              else:
                d3 = tsp[route_path[stage_id+1]][entry_node_index][destination_index]['distance']
              print route_num, stage_id, source_index, exit_node_index, entry_node_index, destination_index, d0, d1, d2, d3
              if (d0 + d1 + d2 + d3 < distance_from_source[route_num][stage_id + 1][destination_index]['distance']):
                node_details = { 'source_index' : source_index, 'exit_node_index' : exit_node_index, 'entry_node_index' : entry_node_index, 'destination_index' : destination_index }  
                distance_from_source[route_num][stage_id + 1][destination_index] = {'distance' : d0 + d1 + d2 +d3, 'node_details' :node_details} 
  return distance_from_source


#md = find_minimal_path_for_route(all_stage_distance_pair, clusters, tsp, visit_order, distance_from_source, hub_lat_lon=[13.023858, 80.163588]) 

def get_grouping(grouping_information):
  # Find a way how effectively we can read the group info.  
  with open(grouping_information) as f:
    lines = f.read()
    cluster_grouping_info = json.loads(lines)
  return cluster_grouping_info
          
def main():
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('--cluster_size', default=21, type=int)
  parser.add_argument('--grouped_output_file_prefix', default="/tmp/routing")
  parser.add_argument('--cluster_input_prefix', default='/tmp/outfile')
  parser.add_argument('--grouping_information', default='/tmp/grouped')

  args = parser.parse_args()
 
  return args


if __name__ == '__main__':
  main()
