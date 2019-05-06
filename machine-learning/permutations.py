#!/usr/bin/python
import argparse
import sys

def nPr(n, r):
  if (r < 0 or n < 0 or r > n):
    raise "Invalid arguments to nPr n = " + n + ", r " + r +"."  
  p = n
  for i in range(r - 1):
    n -= 1
    p *= n
  return p

def _ranked_permutation_recursion(rank, seq,  n, r, depth):
  if r == 1:
    swap = seq[rank + depth]
    seq.remove(swap)
    seq.insert(depth, swap)
    return
  d = nPr(n-1, r-1); 
  q = rank / d;
  rem = rank  % d;
  swap = seq[q + depth]
  # need to push the elements
  seq.remove(swap)
  seq.insert(depth, swap)
  _ranked_permutation_recursion(rem, seq, n - 1, r - 1, depth + 1)

  
def ranked_permutation(rank, n, r):
  if rank < 0 or rank >= nPr(n, r):
    raise BaseException("Invalid arguments to ranked_permutation = " + str(rank) + " for n :" + str(n) + " and " + str(r) + "." ) 
  permutation = range(n)
  _ranked_permutation_recursion(rank, permutation, n, r, 0) 
  return permutation[:r]

def main():
  parser = argparse.ArgumentParser(description="Permutations of integers.")
  parser.add_argument('--n', type=int, default=10)
  parser.add_argument('--r', type=int, default=10)
  parser.add_argument('--rank', type=int, default=-1)

  args = parser.parse_args()
  if args.rank != -1:
    print ranked_permutation(args.rank, args.n, args.r)
    return
  for i in range(nPr(args.n, args.r)):
    print ranked_permutation(i, args.n, args.r)

if __name__ == '__main__':
  main()
