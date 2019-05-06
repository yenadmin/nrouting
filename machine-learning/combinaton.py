#!/usr/bin/python
import argparse
import sys

def nCr(n, r):
  if (r < 0 or n < 0 or r > n):
    raise Exception ("Invalid arguments to nPr n = " + str(n) + ", r " + str(r) +".")
  numerator = 1
  denominator = 1
  if r > n - r:
    r = n - r
  for i in range(1, r + 1):
    numerator *= n
    denominator *= i
    n -= 1
  return numerator / denominator 


def _ranked_combination_recursion(rank, seq,  n, r, pos):
  if r == 0 or n == 0 or rank == 0 or n == r:
    return
  d = nCr(n-1, r-1); 
  elm = seq[pos]
  if rank < d:
    _ranked_combination_recursion(rank, seq, n - 1, r - 1, pos + 1)
  else:
    seq.remove(elm)
    _ranked_combination_recursion(rank - d, seq, n - 1, r, pos)

  
def ranked_combination(rank, n, r):
  if rank < 0 or rank >= nCr(n, r):
    raise "Invalid arguments to ranked_combination = " + rank + "."  
  combination = range(n)
  _ranked_combination_recursion(rank, combination, n, r, 0) 
  return combination[:r]

def main():
  parser = argparse.ArgumentParser(description="Combinations of integers.")
  parser.add_argument('--n', type=int, default=10)
  parser.add_argument('--r', type=int, default=10)

  args = parser.parse_args()
  for i in range(nCr(args.n, args.r)):
    print ranked_combination(i, args.n , args.r)

if __name__ == '__main__':
  main()
