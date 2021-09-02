import generate_graph as gg
from itertools import permutations, combinations_with_replacement

def bitfield(n):
    return [int(digit) for digit in bin(n)[2:]]

def hamming_2(n):
  hamming_set = []
  for i in range(n):
    for j in range(i+1, n):
      set = [0]*n
      set[i] = 1
      set[j] = 1
      hamming_set.append(set)
  return hamming_set

def flatten(t):
    return [item for sublist in t for item in sublist]

def adjacencies(nodes):
    hamming_sets = hamming_2(nodes)
    #set = combinations(hamming_sets, nodes)
    superset = combinations_with_replacement(hamming_sets, nodes)
    #print(list(superset))
    flatset = []
    megaset = []
    for subset in superset:
      megaset.append(permutations(list(subset)))
    for subset in megaset:
      for subsubset in subset:
        #flatset.append(flatten(list(subsubset)))
        flatset.append(list(subsubset))

    #this still returns a lot of duplicates, finding the set of uniques is to be implemented
    return flatset

def mcp_solver(g):
    result = 0
    array = []
    size, edges = g
    for n in range(2**size):
        node_array = bitfield(n)         
        node_array = [0]*(size-len(node_array)) + node_array    
        #node_array.extend([0]*(size-len(node_array)))
        node_array = [-1 if x == 0 else 1 for x in node_array]
        
        
        c = 0
        for e in edges:
            c += 0.5 * (1 - int(node_array[e[0]]) * int(node_array[e[1]]))
           
        if c >= result:
            if c > result:
                array.clear()   
            array.append(''.join(map(str, [0 if x == -1 else 1 for x in node_array])))    
            result = c  
        #print(array)             
        
    return array

def mcp_score(max_size):
    opt_results = [0] * (max_size - 4)
    for i in range(5, max_size+1):
        print(i)
        graph = gg.regular_graph(i)
        opt_results[i - 5] = mcp_solver(graph)
        print(opt_results)
    return opt_results

def dsp_score(graph):
    
    
    result = 0
    c = 0
    size = graph.number_of_nodes()
    edges = [list(edge) for edge in graph.edges()]   
    connections = []
    
    for k in range(size):
        connections.append([k])
    for t in edges:
        connections[t[0]].append(t[1])
        connections[t[1]].append(t[0])
    for n in range(2 ** size):
        node_array = bitfield(n)
        zero_array = [0] * (size - len(node_array))
        node_array = zero_array + node_array
        T = 0
        for con in connections:
            tmp = 0
            for k in con:
                tmp = tmp or node_array[k]
                if tmp:
                    T += 1
                    break
        D = 0
        for j in range(size):
            D += 1 - node_array[j]
        c = (T + D)
        if c >= result:
            result = c
    
    return result

def tsp_score(tsp_graph):
    
    size, A, D = tsp_graph
    coupling = []
    opt_array = []
    result = 10**8
    for i in range(size):
        for j in range(i):
            if i != j:
                #coupling.append([i + j * size, j + i * size])
                coupling.append([j, i])
    print("evaluating all possible configurations, this might take a while.")
    #node_array_set = adjacencies(size)
    node_array_set = tsp_arrays(size)
    for node_array in node_array_set:
        cost = 0
        for i in range(0, size):
            for j in range(0, size):
                #cost += D[i + size * j] * node_array[i + size * j]
                cost += 0.5*D[i*size + j] * node_array[i][j]
        for j in coupling:
            cost += -5 * (1 - 2 * node_array[j[0]][j[1]]) * (1 - 2 * node_array[j[1]][j[0]])
        if cost <= result:
            double_flag = 0;
            # for array in node_array:
            #     if (array.count(1) != 1):
            #         double_flag = 1
            if(not double_flag):        
                print(node_array)
                total = []
                for i in node_array:
                    total += i
                opt_array.append(''.join(map(str, total)))
            result = cost
    opt_results = result
    print(D)
    return opt_results, opt_array

def tsp_arrays(n):
    
    perms =  [list(perm) for perm in permutations(range(3))]
    array_set = []
    
    for perm in perms:
        ones_array = []
        
        for i in range(n):
            ones = []
            for j in range (n):
                ones.append(0)
            ones_array.append(ones)    
        
        
        for i in range(n):
            ones_array[i][perm[i]] = 1
        
        array_set.append(ones_array)
        
    return array_set
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    
