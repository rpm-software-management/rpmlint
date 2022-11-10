#!/usr/bin/env python3

if __name__ == '__main__':
    import sys
    import pstats

    p = pstats.Stats(sys.argv[1])
    N = 60
    p.sort_stats('cumulative').print_stats(N)
    print('========================================================')
    p.sort_stats('tottime').print_stats(N)
    print('========================================================')
    p.sort_stats('ncalls').print_stats(N)
