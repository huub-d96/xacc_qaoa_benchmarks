"""
Created on Thu Aug  5 12:05:10 2021

Auhtor: Huub Donkers
Project: QAOA Benchmarks XACC platform
Description: QAOA for maxcut, travellings salesman and dominating set problem.
             TSP and DSP functions based on work from:
                 https://github.com/koenmesman/benchmark_qaoa_IBM
             This program contains functions to:
                 - Generate MCP, TSP and DSP xacc circuits
                 - Compute cost for MCP, TSP and DSP qubit measurements
                 - Run QAOA using the scipy optimize function ('COBYLA')
                 - Get local and remote runtimes for each QAOA job
                 - Plot measured qubit results (if verbose)
                 - Print optimizer results (if verbose)
"""

import xacc
from math import pi
import extra_gates as gates
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import time
import sys
from qiskit import IBMQ 

#Global provider function to load IBM Accoutn credentials
provider = IBMQ.load_account()

def genTSPCircuit(qpu, qpu_id, graph, params):
    """"
    Parameters:
        qpu : XACC Accelerator Object - Used for circuit compiler
        qpu_id : string - Used to do some additional mapping for IBM backend
        graph : list - Contains information about graph size and edge
        params : list - Parameters beta and gamma used by optimizer

    Returns:
        mapped_program : XACC Composite Intstruction
    """   
    
    compiler = xacc.getCompiler('xasm')
    circuit = '__qpu__ void qaoa_tsp(qbit q){  \n'
    
    p = len(params)//2
    beta = params[:p]
    gamma = params[p:]
    
    num_nodes, A, D = graph
    num_qbits = num_nodes**2
    
    #Set inital state 
    for q in range(num_nodes):
        q_range = range(q*num_nodes, (q+1)*num_nodes)
        circuit += gates.dicke_init(num_nodes, 2, q_range)
    
    #Cost unitary
    for P in range(p):
        for i in range(num_qbits):
            circuit += ('Rz(q[%i], %f); \n' % (i, gamma[P]*D[i]/(2*pi)))
            
        for i in range(num_nodes):
            for j in range(i):
                if i != j:
                    circuit += gates.rzz(20*gamma[P]/pi, j+i*num_nodes, i+j*num_nodes)
    
    #Mixer unitary
        for i in range(0, num_nodes):
            circuit += gates.rxx(-beta[P], i*num_nodes, (i*num_nodes+1))
            circuit += gates.rxx(-beta[P], (i*num_nodes+1), (i*num_nodes+2))

            circuit += gates.ryy(-beta[P], i*num_nodes, (i*num_nodes+1))
            circuit += gates.ryy(-beta[P], (i*num_nodes+1), (i*num_nodes+2))
    
    #Measurements
    for N in range(num_qbits):
        circuit += ('Measure(q[%i]); \n' % N)
    
    #Finish circuit        
    circuit += ('}')
        
    #print(circuit)     
        
    program = compiler.compile(circuit, qpu)
    
    mapped_program = program.getComposite('qaoa_tsp')
    if(qpu_id[0:3] == 'ibm'):
        mapped_program.defaultPlacement(qpu)
        
    return mapped_program

def getTSPExpectation(counts, graph):
    """
    Parameters:
        counts : dict - Number of measurements per qubit bitstring
        graph : list - Contains information about graph size and edge

    Returns:
        total_cost : float - Cost result for certain counts and graph
    """
    
    v, A, D = graph
    
    out_state = counts
    total_count = 0
    total_cost = 0
    for t in out_state:
        count = int(out_state.get(t))
        total_count += count
        bin_len = "{0:0" + str(v) + "b}"  # string required for binary formatting
        bin_val = t.format(bin_len)
        bin_val = [int(i) for i in bin_val]
        cost = 0
        coupling = []
        for i in range(v):
            for j in range(i):
                if i != j:
                    coupling.append([i+j*v, j+i*v])

        for i in range(0, v):
            for j in range(i, v):
                cost += 0.5*D[i + v*j]*bin_val[i + v*j]
        for j in coupling:
            cost += -5*(1 - 2*bin_val[j[0]])*(1 - 2*bin_val[j[1]])
        total_cost += cost*count
        
        total_cost = -total_cost/total_count

    return total_cost


def genDSPCircuit(qpu, qpu_id, graph, params):
    """
    Parameters:
        qpu : XACC Accelerator Object - Used for circuit compiler
        qpu_id : string - Used to do some additional mapping for IBM backend
        graph : list - Contains information about graph size and edge
        params : list - Parameters beta and gamma used by optimizer

    Returns:
        mapped_program : XACC Composite Intstruction
    """   
    
    p = len(params)//2
    beta = params[:p]
    gamma = params[p:]
    
    v, edge_list = graph
    vertice_list = list(range(0, v, 1))

    connections = []
    for i in range(v):
        connections.append([i])
    for t in edge_list:
        connections[t[0]].append(t[1])
        connections[t[1]].append(t[0])
    ancillas = 0
    for con in connections:
        if len(con) > ancillas:
            ancillas = len(con)
    n = v+ancillas         # add ancillas
    
    compiler = xacc.getCompiler('xasm')
    circuit = '__qpu__ void qaoa_dsp(qbit q){  \n'

    for qubit in range(v):
        
        #Initialize to |+>
        circuit +=  ('H(q[%i]); \n' % qubit)
        
        #inverted crz gate
        circuit +=  ('X(q[%i]); \n' % qubit)
        circuit += ('CRZ(q[%i], q[%i], %f); \n' % (qubit, n-1, -gamma[0]))
        circuit +=  ('X(q[%i]); \n' % qubit)
        
    for iteration in range(p):
        f = 0
        f_anc = v
        for con in connections:  # TODO: fix for unordered edges e.g. (2,0)
            c_len = len(con)
            OR_range = con.copy()
            for k in range(c_len-1):
                OR_range.append(v+k)
                
            OR_range.append(n-1)
            
            circuit += gates.OR_nrz(c_len, gamma[p-1], OR_range)

        for qb in vertice_list:
            circuit += ('Rx(q[%i], %f); \n' % (qb, -2*beta[p-1]))
    
    #Measure results
    for N in range(v):
        circuit += ('Measure(q[%i]); \n' % N)
        
    circuit += ('}')  
    
    program = compiler.compile(circuit, qpu)
    
    mapped_program = program.getComposite('qaoa_dsp')
    if(qpu_id[0:3] == 'ibm'):
        mapped_program.defaultPlacement(qpu)
        
    return mapped_program

def getDSPExpectation(counts, graph):
    """
    Parameters:
        counts : dict - Number of measurements per qubit bitstring
        graph : list - Contains information about graph size and edge

    Returns:
        total_cost : float - Cost result for certain counts and graph
    """
    
    v, edge_list = graph   
    vertice_list = list(range(0, v, 1))
    connections = []
    
    for i in range(v):
        connections.append([i])
    for t in edge_list:
        connections[t[0]].append(t[1])
        connections[t[1]].append(t[0])
    total_count = 0
    total_cost = 0
    
    for key in counts:
        count = int(counts.get(key))
        total_count += count
        bin_len = "{0:0" + str(v) + "b}"  # string required for binary formatting
        bin_val = key.format(bin_len)
        bin_val = [int(i) for i in bin_val]
        bin_val.reverse()
        T = 0
        for con in connections:
            tmp = 0
            for k in con:
                tmp = tmp or bin_val[k]
                if tmp:
                    T += 1
                    break
        D = 0
        for i in range(v):
            D += 1 - bin_val[i]
        total_cost += (T+D)*count
    total_cost = -total_cost/total_count
    return total_cost

def genMaxcutCircuit(qpu, qpu_id, graph, params):
    """
    Parameters:
        qpu : XACC Accelerator Object - Used for circuit compiler
        qpu_id : string - Used to do some additional mapping for IBM backend
        graph : list - Contains information about graph size and edge
        params : list - Parameters beta and gamma used by optimizer

    Returns:
        mapped_program : XACC Composite Intstruction
    """
    
    compiler = xacc.getCompiler('xasm')
    circuit = '__qpu__ void qaoa_maxcut(qbit q){  \n'
    
    p = len(params)//2
    beta = params[:p]
    gamma = params[p:]
    
    v, edge_list = graph
    
    #Set inital state to superposition
    for N in range(v):
        circuit += ('H(q[%i]); \n' % N)
    
    for P in range(p):  
            
        #For all edges, set cost Hamiltonian
        for E in edge_list:            
            circuit += ('CX(q[%i], q[%i]); \n' % (E[0], E[1]))
            circuit += ('Ry(q[%i], %f); \n' % (E[1], gamma[P]))
            circuit += ('CX(q[%i], q[%i]); \n' % (E[0], E[1]))
        
        #Apply mixer hamilonian to all qubits    
        for N in range(v):
            circuit += ('Rx(q[%i], %f); \n' % (N, beta[P]))
            
    #Measure results
    for N in range(v):
        circuit += ('Measure(q[%i]); \n' % N)
        
    circuit += ('}')
        
    #print(circuit)     
        
    program = compiler.compile(circuit, qpu)
    
    mapped_program = program.getComposite('qaoa_maxcut')
    if(qpu_id[0:3] == 'ibm'):
        mapped_program.defaultPlacement(qpu)
        
    return mapped_program


def getMaxcutExpectation(counts, graph):
    """
    Parameters:
        counts : dict - Number of measurements per qubit bitstring
        graph : list - Contains information about graph size and edge

    Returns:
        total_cost : float - Cost result for certain counts and graph
    """
    
    def maxcut_obj(x, graph):
        
        edge_list = graph[1]
        obj = 0
        for i, j in edge_list:
            if x[i] != x[j]:
                obj -= 1
                
        return obj
    
    avg = 0
    sum_count = 0
    for bitstring, count in counts.items():
        
        obj = maxcut_obj(bitstring, graph)
        avg += obj * count
        sum_count += count
        
    return avg/sum_count

def getOptFunction(qpu, graph, buffer, qpu_id, circuitFunc, expFunc, job_runtimes):
    """
    Parameters:
        qpu : XACC Accelerator Object - Used for circuitFunc       
        graph : list - Contains information about graph size and edge
        buffer : XACC AcceletorBuffer Object - Used to store QPU results
        qpu_id : string - Used for circuitFunc
        circuitFunc : function - Circuit funtion to generate problem circuit
        expFunc : function - Expectation function to compute cost
        job_runtimes : list - List to store job runtimes

    Returns:
        execute_circuit: function - Used by optimizer to execute QPU
    """
        
    def execute_circ(params):
        
        program = circuitFunc(qpu, qpu_id, graph, params)
        
        start = time.time()
        qpu.execute(buffer, program)        
        job_runtimes.append(getRuntime(qpu_id, buffer, start))
        results = buffer.getMeasurementCounts()
        
        expectation = expFunc(results, graph) 
        
        return expectation
    
    return execute_circ

def getRuntime(qpu_id, buffer, start):
    """
    Parameters:
        qpu_id : string - Used to determine where to get runtime information
        buffer : XACC AcceletorBuffer Object - Used to read QPU information
        start: float - Start time of QAOA job
        
    Returns:
        runtime : float - Runtime of a backend in ms
    """
    
    runtime = 0
    end = time.time()
    
    #IBM runtimes:  
    if(qpu_id[0:3] == 'ibm'): #Remote runtime        
        
        #Receive IBM job results via qiskit
        ibm_backend = qpu_id[4:]
        backend = provider.get_backend(ibm_backend)
        ID = buffer.getInformation().get('ibm-job-id')
        
        #Retreive job information
        while(1):
            job = backend.retrieve_job(ID)
            times = job.time_per_step()
            t_complete = times.get('COMPLETED')
            t_run = times.get('RUNNING')
            if(type(t_complete) ==  type(t_run)): #Sometimes, complete time is not retreived properly
                break
            print('Refetch ibm job information...')
        
        #Compute runtime
        timeDelta = t_complete - t_run
        runtime = timeDelta.total_seconds()*1000 #s to ms
    
    elif(qpu_id == 'ionq'):
        import requests
        key = open('/home/huub/.ionq_config').readline().split(':')[1].strip()
        headers = {'Authorization': 'apiKey '+str(key)}
        params = {'limit': 1} #Only retrieve most recent job execution
        response = requests.get('https://api.ionq.co/v0.1/jobs/', headers=headers, params=params)
        runtime = response.json().get('jobs')[0].get('execution_time')
    
    elif(qpu_id in ['aer', 'qsim', 'qpp']): #Local runtime
        runtime = (end - start)*1000 #s to ms
        
    else:
        sys.exit("Unkown QPU ID!")
    
    return runtime

def runQAOA(qpu, qpu_id, graph, problem, p, verbose = True):
    """
    Parameters:
        qpu : XACC Accelerator Object - Used to generate optimizer function  
        qpu_id : string - Used to generate optimizer function
        graph : list - Contains information about graph size and edge
        problem : string - Sets problem to be used (maxcut, TSP, DSP)
        p : int - Iterations used in QAOA circuit generation
        verbose : bool - If true, print optimizer results and draw QAOA counts
    
    Returns:
        result_list : list - Returns 8 best bitstring QAOA results
        job_runtimes : list - Returns all job runtimes for QAOA optimization        
    """
    
    #Setup QAOA objects and required problem functions
    nodes = graph[0]
    
    if(problem == 'maxcut'):
        circuitFunc = genMaxcutCircuit
        expFunc = getMaxcutExpectation
        n_qbits = nodes      
    elif(problem == 'TSP'):
        circuitFunc = genTSPCircuit
        expFunc = getTSPExpectation
        n_qbits = nodes**2
    elif(problem == 'DSP'):
        circuitFunc = genDSPCircuit
        expFunc = getDSPExpectation
        n_qbits = 2*nodes
    else:
        sys.exit('Unknown problem set: Exit...')
        
    buffer = xacc.qalloc(n_qbits)
    
    #Find optimal values
    job_runtimes = []
    optFunc = getOptFunction(qpu, graph, buffer, qpu_id, circuitFunc, expFunc, job_runtimes)
    initParams = [1.0]*2*p
    optResult = minimize(optFunc, initParams, method='COBYLA')
    if verbose : print(optResult) 
    optParams = optResult.x
    
    #Show results
    program = circuitFunc(qpu, qpu_id, graph, optParams)
    qpu.execute(buffer, program)
    results = buffer.getMeasurementCounts()
    
    #Plot results
    if verbose :
        plt.figure()
        plt.bar(results.keys(), results.values(), color='b')
        plt.xticks(rotation=45, ha='right')
        plt.show()
    
    #Sort results
    results = dict(sorted(results.items(), key = lambda item: item[1], reverse=True)) #Return sorted list
    result_list = [k for k in results.keys()]
    
    return result_list[:8], job_runtimes




        
        
        