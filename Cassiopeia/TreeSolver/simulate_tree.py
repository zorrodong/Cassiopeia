from __future__ import division

import numpy as np
import pandas as pd
import random
from pylab import *
import pickle as pic

import Bio.Phylo as Phylo
import networkx as nx

import sys
import os

import argparse

from Cassiopeia.TreeSolver import *
from Cassiopeia.TreeSolver.lineage_solver import *
from Cassiopeia.TreeSolver.simulation_tools import *

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("out_fp", type=str, help="Output file path")
    parser.add_argument('--subsample_percentage', default=0.4, help="Percentage of cells to sample from final pool")
    parser.add_argument("--depth", "-d", default=10, help='Depth of Tree to Simulate')
    parser.add_argument('--dropout_rate', "-dr", default=None, help="Dictionary of dropout rates per character")
    parser.add_argument("--num_characters", "-c", default=40, help='Number of characters to simulate')
    parser.add_argument("--num_states", "-s", default=10, help="Number of states to simulate")
    parser.add_argument("--mutation_rate", '-m', default=0.025, help="Mutation rate, assumed to be constant across all characters")
    parser.add_argument("--allele_table", default=None, help="Optional alleletable to provide, where parameters will be estimated from")

    args = parser.parse_args()
    output_file = args.out_fp
    subsample_percentage = args.subsample_percentage 
    depth = args.depth
    number_of_characters = args.num_characters
    number_of_states = args.num_states
    dropout_rates = args.dropout_rate
    mutation_rate = args.mutation_rate
    allele_table = args.allele_table


    if allele_table is not None:
        at = pd.read_csv(allele_table, sep='\t')
        piv = pd.pivot_table(at, index=["cellBC"], columns=["intBC"], values="UMI", aggfunc=size)

        if dropout_rates is None:

            dropouts = piv.apply(lambda x: x.isnull().sum() / len(x), axis=0)

        nunique_chars = []
        for n, g in at.groupby(["intBC"]):
        
            nunique_chars.append(len(unique(g["r1"])))
            nunique_chars.append(len(unique(g["r2"])))
            nunique_chars.append(len(unique(g["r3"])))

        number_of_characters = piv.shape[1] * 3 # num char = num intbc * 3
        number_of_states = np.median(nunique_chars)
        
    no_mut_rate = 1 - mutation_rate
    prior_probabilities = {}
    for i in range(0, number_of_characters):
	sampled_probabilities = sorted([np.random.negative_binomial(5,.5) for _ in range(1,number_of_states)])
	prior_probabilities[i] = {'0': no_mut_rate}
	total = np.sum(sampled_probabilities)
	for j in range(1, number_of_states):
		prior_probabilities[i][str(j)] = (mutation_rate)*sampled_probabilities[j-1]/(1.0 * total)

    with open("prior_probs.txt", "w") as f:
        
        for i in range(0, number_of_characters):
            f.write(str(i))

            for j in range(1, number_of_states):
                f.write("\t" + str(prior_probabilities[i][str(j)]))

            f.write("\n")

        f.write("\n")

    if dropout_rate is not None:
        dropouts = pd.read_csv(dropout_rate, sep='\t', index_col = 0) 

    else:
        dropouts = pd.DataFrame(np.full((number_of_characters, 1), 0.1, dtype=float))

    print("Simulating with " + str(number_of_characters) + " Characters and " + str(number_of_states) + " Unique States")
    print("Depth: " + str(depth) + "\nSubsample percentage: " + str(subsample_percentage))
    print("Dropout probabilities:")
    print(dropouts)

    # Generate dropout probabilities
    data_dropout_rates = {}
    j = 0
    for i in range(number_of_characters):
        if allele_table is not None:
            if i != 0 and i % 3 == 0:
                j += 1
            data_dropout_rates[i] = float(dropouts.iloc[j])
        else:
            data_dropout_rates[i] = float(dropouts.iloc[i])

    dropout_prob_map = {i: np.random.choice(data_dropout_rates.values()) for i in range(0,number_of_characters)}

    # Generate simulated network
    true_network = generate_simulated_full_tree(prior_probabilities, dropout_prob_map,characters=number_of_characters, subsample_percentage=subsample_percentage, depth=depth)
    pic.dump(true_network, open(output_file, "wb"))

#target_nodes_original_network = get_leaves_of_tree(true_network, clip_identifier=False)

#k = map(lambda x: "s" + x.split("_")[-1], target_nodes_original_network)
#s_to_char = dict(zip(k, target_nodes))

#with open("phylo.txt", "w") as f:

#    f.write("cellBC")
#    for i in range(number_of_characters):
#        f.write("\t" + str(i))
#    f.write("\n")

#    for n in target_nodes_original_network:
#        charstring, sname = n.split("_")
#        f.write(sname)
#        chars = charstring.split("|")
#        for c in chars:
#            f.write("\t" + c)
#        f.write("\n")

#print("Simulation written to " + output_file)

#print "CCI complexity of reconstruction: ", cci_score(target_nodes)

# Hybrid solution
#reconstructed_network_greedy = solve_lineage_instance(target_nodes, method="greedy", prior_probabilities=prior_probabilities)
#reconstructed_network_hybrid = solve_lineage_instance(target_nodes, method="hybrid", hybrid_subset_cutoff=100, time_limit=1000)

# run camin-sokal
#os.system("python2 binarize_multistate_charmat.py phylo.txt infile") 
# run phylip mix with camin-sokal
#inputs = [b"R", b"P", b"Y", b"R"]
#parent, fd = fork()
#if not parent:
#    os.execv("~/software/phylip-3.697/exe/mix")

#for each in inputs:
#    os.write(fd, each+b'\n')
#    sleep(0.5)

#tree = Phylo.parse("outtree", "newick").next()
#cs_net = net = Phylo.to_networkx(tree)

# convert labels to strings, not Bio.Phylo.Clade objects
#c2str = map(lambda x: str(x), cs_net.nodes())
#c2strdict = dict(zip(cs_net.nodes(), c2str))
#cs_net = nx.relabel_nodes(cs_net, c2strdict)

# convert labels to characters for triplets correct analysis
#cs_net = nx.relabel_nodes(cs_net, s_to_char)


#print "Number of triplets correct greedy: ", check_triplets_correct(true_network, reconstructed_network_greedy)
#print "Number of triplets correct hybrid: ", check_triplets_correct(true_network, reconstructed_network_hybrid)
#print "Camin-Sokal triplets correct: ", check_triplets_correct(true_network, cs_net)
