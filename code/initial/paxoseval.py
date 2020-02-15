import argparse, time, os, subprocess
import numpy as np
import matplotlib.pyplot as plt
from env import Env

ITERATIONS = 5

def plot_graph_as_pdf(clients, tps, variance):
    plt.figure()
    plt.errorbar(clients, tps, yerr=variance, ecolor='black', color='black', fmt='-', capsize=8)
    plt.xlabel('Number of Concurrent Clients')
    plt.xticks(np.arange(min(clients), max(clients)+1, 1.0))
    plt.ylabel('TPS')
    plt.ylim(ymin=0)
    plt.savefig("result.pdf")


if __name__ == '__main__':

    # Get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--size", help="size of cluster", action="store", type=int, default=3)
    parser.add_argument("-c", "--clients", help="number of concurrent clients (proposals)", action="store", type=int, default=10)
    args = parser.parse_args()

    x_clients = []
    y_tps = []
    std = []

    for i in range(1, args.clients+1):
        print ""

        x_clients.append(i)

        # Run experiment three times for each # of concurrent clients
        tps = []
        for _ in range(ITERATIONS):
            s = subprocess.check_output('python env.py -s %d -c %d' % (args.size, i), shell = True, stderr=subprocess.STDOUT)

            current_tps = float(s.decode("utf-8")[0:6])
            tps.append(current_tps)
            
            print "TPS with", i, "clients: ", current_tps
            
            time.sleep(4)

        y_tps.append(np.mean(tps))
        std.append(np.std(tps))

    plot_graph_as_pdf(x_clients, y_tps, std)

    print "\nDone! The resulting plot can be seen in the file \"result.pdf\" \n \n"