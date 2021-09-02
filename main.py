#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 12:31:58 2021

Auhtor: Huub Donkers
Project: QAOA for maxcut
Description: Benchmark for IonQ simulator

"""

import QAOA as qaoa
import exact_solver as exact
import generate_graph as gg
import xacc
import runtime_plots as plot

# Get access to the desired QPU and
# allocate some qubits to run on
qpu_ids = ['qpp', 'qsim', 'aer', 'ionq'] #'ibm:ibmq_qasm_simulator', ionq

graph_sizes = [5 ,7, 9, 11, 13]

#Run QAOA
problem = 'maxcut' #maxcut, TSP, DSP  
p = 1

backend_runtimes = []
for qpu_id in qpu_ids:
    
    #Configure accelerator
    qpu = xacc.getAccelerator(qpu_id, {'shots' : 2048}) 
    
    #Declare empty runtime list and start simulations    
    runtimes_list = []    
    print("Start "+str(qpu_id)+" simulations:")
    for size in graph_sizes:    
        
        #Genererate appropriate graph for problem set
        if(problem !='TSP'):
            graph = gg.regular_graph(size)
            #plot.draw_graph(graph)
        else:
            graph = gg.tsp_problem_set(size, gg.regular_graph)    
            #TODO: DRAW network            
        
        #Run QAOA algorithm
        qaoa_result, job_runtimes = qaoa.runQAOA(qpu, qpu_id, graph, problem, p, False) #List of 8 best solutions & average runtime
        
        #Print & store results
        print("QAOA: ", qaoa_result)
        runtimes_list.append(job_runtimes)
    
    #Store results
    backend_runtimes.append(runtimes_list)
    
#Plot results
title = "Benchmark: " + str(problem) +" problem, p="+str(p)
plot.lineplot_results(backend_runtimes, graph_sizes, title, qpu_ids)

