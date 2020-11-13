if __name__ == '__main__':
    import sys
    import pstats

    p = pstats.Stats(sys.argv[1])
    N = 60
    p.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(N)
    print('========================================================')
    p.sort_stats(pstats.SortKey.PCALLS).print_stats(N)
