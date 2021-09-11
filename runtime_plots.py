"""
Created on Tue Aug 31 20:29:26 2021

Auhtor: huub-d96
Project: QAOA Benchmarks XACC platform
Description: Functions to visualize benchmark resuts using matplotlib and 
             draw graphs using networkx
"""

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.ticker import FixedLocator


def draw_graph(g):
    """
    Parameters:
    g : list - input graph containing graph size and edge information

    Returns: 
        none
    """
    
    graph = nx.Graph()
    graph.add_nodes_from(range(g[0]))
    graph.add_edges_from(g[1])
    nx.draw_circular(graph, with_labels=True, alpha=0.8, node_size=500)
    

def lineplot_results(backend_runtimes, graph_sizes, title, legend = []):
    """
    Parameters:
        backend_runtimes : nested list - Runtime resuls of multiple backends
        graph_sizes : list - sizes of graph used in benchmark
        title : string - Main plot title, based on problem and p
        legend : list - qpu_ids used in benchmark

    Returns: 
        none
    """
        
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
    fig.set_size_inches(8,4)
    
    for runtimes_list in backend_runtimes:
        means = []
        iters = []
        totals = []
        for runtimes in runtimes_list:
            means.append(sum(runtimes)/len(runtimes))
            iters.append(len(runtimes))
            totals.append(sum(runtimes)/1000) #ms to s
        ax1.plot(graph_sizes, means, marker = 'o') 
        ax2.plot(graph_sizes, iters, marker = 'o') 
        ax3.plot(graph_sizes, totals, marker = 'o')
      
    
    # Force x-axis integers
    ax1.xaxis.set_major_locator(FixedLocator(graph_sizes))
    ax2.xaxis.set_major_locator(FixedLocator(graph_sizes))
    ax3.xaxis.set_major_locator(FixedLocator(graph_sizes))
    
    #y-axis scale
    ax1.set_yscale("log")
    ax3.set_yscale("log")
    #ax.set_ylim([10**(-1), 10**6])
     
    # Adding title
    fig.suptitle(title)
    ax1.set_title('Average job runtime')
    ax1.set_xlabel("Nodes")
    ax1.set_ylabel("Runtime [ms]")
    
    ax2.set_title('Optimizer iterations')
    ax2.set_xlabel("Nodes")
    ax2.set_ylabel("Iterations")
    
    ax3.set_title('Total QAOA runtime')
    ax3.set_xlabel("Nodes")
    ax3.set_ylabel("Runtime [s]")
    
    #Add legend
    legend_copy = legend.copy()
    for i, qpu in enumerate(legend_copy):
        if qpu in ['aer', 'qsim', 'qpp']:
            legend_copy[i]= qpu +' (local)'
    fig.legend(legend_copy, loc='upper center', bbox_to_anchor=(0.5, 0.05),
          fancybox=True, shadow=True, ncol=5)
     
    # Removing top axes and right axes
    # ticks
    ax1.get_xaxis().tick_bottom()
    ax1.get_yaxis().tick_left()
    
    fig.tight_layout()
    
    plt.savefig("plots/"+"".join(title.split(" "))+".pdf", bbox_inches='tight')

#TODO: Update boxplots for multiple backends
def boxplot_results(runtimes_list, graph_sizes, title):
    """
    Parameters:
        runtimes_list : list - Runtime resuls of single backend
        graph_sizes : list - sizes of graph used in benchmark
        title : string - Main plot title, based on problem and p

    Returns: 
        none
    """
    fig = plt.figure(figsize =(10, 7))
    ax = fig.add_subplot(111)
     
    # Creating axes instance
    bp = ax.boxplot(runtimes_list, patch_artist = True)
     
    colors = ['#0000FF', '#00FF00',
              '#FFFF00', '#FF00FF']
     
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
     
    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color ='#8B008B',
                    linewidth = 1.5,
                    linestyle =":")
     
    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color ='#8B008B',
                linewidth = 2)
     
    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color ='red',
                   linewidth = 3)
     
    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker ='D',
                  color ='#e7298a',
                  alpha = 0.5)
         
    # x-axis labels
    ax.set_xticklabels(graph_sizes)
    
    #y-axis scale
    plt.yscale("linear")
     
    # Adding title
    plt.title(title)
    plt.xlabel("Nodes")
    plt.ylabel("Runtime [ms]")
     
    # Removing top axes and right axes
    # ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
         
    # show plot
    plt.show(bp)