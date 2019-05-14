#!/usr/bin/python

from sklearn import datasets
from sklearn.cluster import KMeans

import argparse
import csv
import json
import marshal
import time
import pandas as pd
#import matplotlib.pyplot as plt
import group_clusters
import get_geocodes
import permutations

COLOURS = ['b', 'g', 'y', 'r', 'c', 'm', 'k']
MARKERS = ['o', '^', '+', 'v', 'x', 's', 'd']  #  In case if we need more , '*', 'p', '>', '<', '.' and 'h' hex reserved for source 

def location_clusters(geogroup, data_train): 
  clusters= {}
  for i in geogroup.keys():
    grouped = []
    for dataobject in geogroup[i]:
      grouped.append(data_train[data_train.index == dataobject])
    clusters[i] = pd.concat(grouped) 
  return clusters

"""
def plot_individual_clusters(clusters, source):
  fig, ax = plt.subplots()
  for key,geocluster in clusters.iteritems():
    print key, COLOURS[key/len(COLOURS)], MARKERS[key%len(MARKERS)] 
    df = geocluster[['latitude', 'longitude', 'Cust ID']]
    df.plot(ax=ax, kind='scatter', y='latitude', x='longitude',
            c=COLOURS[key/len(COLOURS)],
            marker=MARKERS[key%len(MARKERS)], s=64)
    lon = df.longitude.to_list()
    lat = df.longitude.to_list()
    cust = df['Cust ID'].to_list()
    for i in range(len(cust)):
      ax.text( lon[i], lat[i], cust[i], fontsize=9)
  df  = pd.DataFrame(columns=['latitude', 'longitude' ], data=[source])
  df.plot(ax=ax, kind='scatter', y='latitude', x='longitude',
            c='m', marker='h', s=200)
  plt.show()
"""

def print_labels(labels):
  geogroup = {}
  for i in range(len(labels)):
    group = geogroup.get(labels[i], [])
    group.append(i)
    geogroup[labels[i]] = group
  print "Cluster details"
  for i in geogroup.keys():
    print i, len(geogroup[i])
  return geogroup


def kmeans_cluster(cluster_size, randomness, tolerance, iteration, data):
  kmeans = KMeans(n_clusters=cluster_size, random_state=randomness,
                tol=tolerance,
                max_iter=iteration, algorithm='full').fit(data)
  geogroup = print_labels(kmeans.labels_)
  return kmeans, geogroup

def create_cluster(args):
  data_train = pd.read_csv(args.tsv_file, sep='\t')
  train_data = data_train[['latitude', 'longitude']]
  
  kmeans, geocluster = kmeans_cluster(args.cluster_size,
                    args.randomness,
                    args.tolerance,
                    args.iterations, train_data)
  clusters = location_clusters(geocluster, data_train)
  return kmeans, clusters

def save_cluster(filepath, clusters, min_dist,
              visit_order, all_stage_distance_pair, 
              distance_from_source, tsp, tsp_cluster, route_stages, stages):
  for key in clusters.keys():
    with open(filepath + str(key) + ".tsv" , "wb") as f:
      # Just adding index in header for tabs to be appropriate
      f.write("index");
      f.write(clusters[key].to_csv(sep='\t'))
  with open(filepath +  "_visit_order.marshal", "wb") as f:
    marshal.dump(visit_order, f)
  with open(filepath +  "_all_stage_distance_pair.marshal", "wb") as f:
    marshal.dump(all_stage_distance_pair, f)
  with open(filepath +  "_distance_from_source.marshal", "wb") as f:
    marshal.dump(distance_from_source, f)
  with open(filepath +  "_tsp.marshal", "wb") as f:
    marshal.dump(tsp, f)
  with open(filepath +  "_tsp_cluster.marshal", "wb") as f:
    marshal.dump(tsp_cluster, f)
  with open(filepath +  "_route_stages.marshal", "wb") as f:
    marshal.dump(route_stages, f)
  with open(filepath +  "_stages.marshal", "wb") as f:
    marshal.dump(stages, f)
  print "wrote " + str(len(clusters)) + " records."

def print_single_node(nodes, cluster, stage_tsp, source, out_file):
  mininum = get_geocodes.MAXIMUM_METERS
  cutomer_order_list = []
  n = len(cluster) 
  for i in range(n):
    for j in range(n):
      if i == j: continue
      d0 = nodes[i]['distance']
      if d0 + stage_tsp[i][j]['distance'] < mininum:
        mininum = d0 + stage_tsp[i][j]['distance']
        rank = stage_tsp[i][j]['rank']
  permutation = permutations.ranked_permutation(rank, n , n)  
  for j in range(n - 1, -1, -1):
    cutomer_order_list.append(cluster.iloc[permutation[j]])
  print_customers(cutomer_order_list, source, out_file) 

def get_min_node(cluster_nodes, link = None):
  minimum = get_geocodes.MAXIMUM_METERS
  for k, v in cluster_nodes.iteritems():
    d1 = link[k][0] if link != None else 0
    d2 = v['distance']
    if d1 + d2 < minimum:
      minimum = d1 + d2 
      node_details = v['node_details']
  return node_details 
  
def print_path(md, visit_order, clusters, tsp, all_stage_distance_pair,  source, out_file):
  for route_num in md.keys():
    out_file.write("<br><h4>Routing details for route %d <h4><br>" % (route_num + 1))
    out_file.write("-----------------------------------------<br>")
    cutomer_order_list =[]
    if len(md[route_num]) == 1:
      print_single_node(md[route_num][0], clusters[visit_order[route_num][0]], tsp[visit_order[route_num][0]], source, out_file)
      continue  
    last = md[route_num][len(md[route_num])-1]
    node_details = get_min_node(last)
    i = len(md[route_num])-1
    if (len(tsp[visit_order[route_num][i]]) == 0):
      cutomer_order_list.append(clusters[visit_order[route_num][i]].iloc[0])
    else:
      r = tsp[visit_order[route_num][i]][node_details['entry_node_index']][node_details['destination_index']]['rank']
      n = len(clusters[visit_order[route_num][i]])
      permutation = permutations.ranked_permutation(r, n , n)  
      for j in range(n - 1, -1, -1):
        cutomer_order_list.append(clusters[visit_order[route_num][i]].iloc[permutation[j]])
    for i in range(len(md[route_num])-2, -1, -1):
      if (len(tsp[visit_order[route_num][i]]) == 0):
        cutomer_order_list.append(clusters[visit_order[route_num][i]].iloc[0])
        if (i > 0):
          node_details = get_min_node(md[route_num][i],  all_stage_distance_pair[route_num][i ]) 
        continue
      #else:
      entry_node = node_details['entry_node_index']
      exit_node = node_details['destination_index']
      stage_exit_node = node_details['exit_node_index']
      source_node = node_details['source_index']
      if route_num == 6: 
        print i, source_node, stage_exit_node 
      r = tsp[visit_order[route_num][i]][source_node][stage_exit_node]['rank']
      n = len(clusters[visit_order[route_num][i]])
      permutation = permutations.ranked_permutation(r, n , n)  
      for j in range(n - 1, -1, -1):
        cutomer_order_list.append(clusters[visit_order[route_num][i]].iloc[permutation[j]])
      if i == 0: break
      node_details = md[route_num][i ][stage_exit_node]['node_details']
    print_customers(cutomer_order_list, source, out_file)

def print_customers(cutomer_order_list, source, out_file):
  url = "https://www.google.com/maps/dir"
  url = url + "/%3.7f,%3.7f"  % (source[0], source[1])
  out_file.write("<h5>Optimal visit Order</h5><table>")
  out_file.write("<tr><th>Seq No</th><th>Name</th><th>Address</th><th>Location</th></tr>")
  for i in range(len(cutomer_order_list)):
    cust = cutomer_order_list.pop()
    lat_lon = "%3.7f,%3.7f"  % (cust.latitude, cust.longitude)
    url += "/" + lat_lon
    out_file.write("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td>" % (i + 1, cust['Customer Name'] , cust['address'], lat_lon ))
  out_file.write("</table> <br> <b> <a href=%s/> Routing Url </a></b> <br>" % url)
    

def main():
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('--cluster_size', default=21, type=int)
  parser.add_argument('--randomness', default=1, type=int)
  parser.add_argument('--tolerance', default=4, type=int)
  parser.add_argument('--iterations', default=300, type=int)
  parser.add_argument('--num_routes', default=6, type=int)
  parser.add_argument('--tsv_file', default="/tmp/geocoded.tsv")
  parser.add_argument('--cluster_output_prefix', default='/tmp/outfile')
  parser.add_argument('--grouping_information', default='/tmp/grouped')
  parser.add_argument('--source_lat_lon', default='13.023858,80.163588')
  parser.add_argument('--compute_metrix', default=True, type=bool)


  args = parser.parse_args()
  #return args
  kmeans, clusters = create_cluster(args)
  # Thi Will bock the call and untll this the graph is closed next line will not be executed.

  # Try changing it with nargs='+' in args parser
  source_str = args.source_lat_lon.split(",")
  if len(source_str) != 2:
    print "Error in the lat lon string"
    exit(0)
  source = [float(source_str[0]), float(source_str[1])]
  #plot_individual_clusters(clusters, source=source)
  #y=raw_input("Enter y to continue : ")
  #if y[0] != 'y' and  y[0] != 'Y':
  #  exit(0)

  # using this advantage group the cluster and write it to a file args.grouping_information
  #cluster_grouping_info = group_clusters.get_grouping(args.grouping_information)
  points = [source] 
  points.extend(kmeans.cluster_centers_.tolist())
  all_pair_centroid_metric = group_clusters.compute_all_pair_centroid_metric(points)

  cluster_grouping_info = group_clusters.compute_groups(all_pair_centroid_metric, args.num_routes)
  
  centroid_paths = group_clusters.centroids_group_df(cluster_grouping_info, kmeans, 
                                                     hub_lat_lon=source)
  stages = group_clusters.compute_distance_metrics(clusters)
  #time.sleep(10)
  route_stages = group_clusters.compute_distance_metrics(centroid_paths)
  #time.sleep(30)
  tsp_cluster = group_clusters.all_pair_tsp(route_stages)
  #time.sleep(10)
  routes = group_clusters.find_min_path(tsp_cluster)
  #time.sleep(20)
  tsp = group_clusters.all_pair_tsp(stages)
  #time.sleep(20)
  visit_order =  group_clusters.find_visit_order(routes, cluster_grouping_info)
  #time.sleep(10)
  distance_from_source = group_clusters.find_distance_from_sourcee(clusters, visit_order, 
                                                                   hub_lat_lon=source)
  #time.sleep(10)
  all_stage_distance_pair = group_clusters.find_pair_wise_distance_for_cluster(visit_order,  clusters)

  min_dist = group_clusters.find_minimal_path_for_route(all_stage_distance_pair, clusters, tsp, 
                                                        visit_order, distance_from_source, 
                                                        hub_lat_lon=source) 
  with open (args.cluster_output_prefix + "routing.txt", "wb") as out_file:
    print_path(min_dist, visit_order, clusters, tsp, all_stage_distance_pair, source, out_file)

  save_cluster(args.cluster_output_prefix,
              clusters, min_dist, 
              visit_order, all_stage_distance_pair, distance_from_source,
              tsp, tsp_cluster, route_stages, stages)
  
  return args


if __name__ == '__main__':
  main()
