if __name__ == '__main__':
    import sys
    import pstats

    p = pstats.Stats(sys.argv[1])
#    stats.strip_dirs()
    p.sort_stats('cumulative').print_stats(60)
    print('========================================================')
    p.sort_stats('ncalls').print_stats(60)
