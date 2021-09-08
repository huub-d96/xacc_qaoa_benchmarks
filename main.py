"""
Created on Sat Aug 21 12:31:58 2021

Auhtor: huub-d96
Project: QAOA Benchmarks XACC platform
Description: This program collects runtime data for different QPU simulator 
             backends (or physical backends) using the XACC platform. 
             Three benchmarks have been implemented for QAOA:
                 - Maxcut problem
                 - Travelling salesman problem
                 - Dominating set problem
"""

import QAOA as qaoa
#import exact_solver as exact #Currently not used for benchmarking
import generate_graph as gg
import xacc
import runtime_plots as plot
import pickle
from os import listdir
from os.path import isfile, join

""""BENCHMARK PARAMETERS TO EDIT """
# Get access to the desired QPU and
# allocate some qubits to run on
qpu_ids = ['ibm:ibmq_qasm_simulator', 'aer', 'qsim', 'ionq'] #, 'qpp', 'qsim', 

#Setup QAOA circuit parameters
#Set of graph sizes for problems (>15 qbits takes long time for local simulators)
problem_set = [
               #['DSP', [5, 7, 9, 11, 13, 15, 17, 19]],
               ['TSP', [3, 4]], #, 5]],
               ['maxcut', [5 ,7, 9, 11, 13, 15, 17, 19, 21, 23, 25]]
               ] #maxcut, TSP, DSP  

p = 1  #Increasing p usually improves QAOA score, but also drastically incraeses simulation time

"""END OF EDIT"""

#Get list of acquired data
data_list = [f for f in listdir("./data") if isfile(join("./data", f))]

for problem, graph_sizes  in problem_set:
    
    for qpu_id in qpu_ids:
        
        #Configure accelerator
        qpu = xacc.getAccelerator(qpu_id, {'shots' : 2048})        
        
        #Declare empty runtime list and start simulations
        runtimes_list = []    
        print("Start "+str(qpu_id)+" simulations:")
        for size in graph_sizes:
            
            #Run ID
            num_str = '0'+str(size) if size < 10 else str(size)
            run_id = str(problem)+'-'+str(qpu_id)+'-size-'+num_str+'-p'+str(p)
            
            #Check if data is allready available
            
            if run_id not in data_list:  
            
                #Genererate appropriate graph for problem set
                if(problem !='TSP'):
                    graph = gg.regular_graph(size)
                    #plot.draw_graph(graph)
                else:
                    graph = gg.tsp_problem_set(size, gg.regular_graph)    
                    #TODO: DRAW network            
                
                #Run QAOA algorithm
                qaoa_result, job_runtimes = qaoa.runQAOA(qpu, qpu_id, graph, problem, p, False) #List of 8 best solutions & average runtime
                
                #Fix ibm errors
                if qpu_id[0:3] == 'ibm':
                    for i in range(len(job_runtimes)):
                        if job_runtimes[i] == 0:
                            job_runtimes[i] = (job_runtimes[i-1] + job_runtimes[i+1])/2
                            #TODO: Fix edge cases
                        
                
                #Print & store results
                print("QAOA: ", qaoa_result)
                #runtimes_list.append(job_runtimes)
        
                #Store results
                with open('./data/'+run_id, "wb") as fp:
                    pickle.dump(job_runtimes, fp)
        
        #backend_runtimes.append(runtimes_list)
        
    #Retrieve stored data
    data_list = sorted([f for f in listdir("./data") if isfile(join("./data", f))])
    backend_runtimes = []
    for qpu_id in qpu_ids:        
        runtimes_list = []
        for filename in data_list:
            index = filename.split('-')
            if (index[0] == problem and index[1] == qpu_id and int(index[3]) in graph_sizes):                
                runtimes_list.append(pickle.load(open('./data/'+filename, "rb")))
        backend_runtimes.append(runtimes_list)
    
    #Plot results        
    title = "Benchmark: " + str(problem) +" problem, p="+str(p)
    plot.lineplot_results(backend_runtimes, graph_sizes, title, qpu_ids)
    
    #Store final results
    with open("data_"+str(problem)+"_p"+str(p), "wb") as fp:
        pickle.dump(backend_runtimes, fp)
        
print("Benchmarking finished!")

