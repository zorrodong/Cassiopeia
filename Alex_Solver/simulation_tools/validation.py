from collections import defaultdict
import networkx as nx
import random

from simulation_utils import get_leaves_of_tree

def tree_collapse(graph):
	"""
	Given a networkx graph in the form of a tree, collapse two nodes togethor if there are no mutations seperating the two nodes
	:param graph: Networkx Graph as a tree
	:return: Collapsed tree as a Networkx object
	"""
	new_network = nx.DiGraph()
	for edge in graph.edges():
		if edge[0].split('_')[0] == edge[1].split('_')[0]:
			for node in graph.successors(edge[1]):
				new_network.add_edge(edge[0], node)
		else:
			new_network.add_edge(edge[0], edge[1])
	return new_network

def check_triplets_correct(simulated_tree, reconstructed_tree, number_of_trials=10000, dict_return=False):
	"""
	Given a simulated tree and a reconstructed tree, calculate the percentage of triplets that have
	the same structure in both trees via random sampling of triplets
	:param simulated_tree:
		Networkx tree generated by simulation method in simulation_tools/dataset_generation.py
	:param reconstructed_tree:
		Reconstructed tree generated by reconstruction tools in lineage_solver/lineage_solver.py
	:param number_of_trials:
		The number of triplets to test
	:param dict_return:
		Whether to return the frequency and correctness across the various depths during the simulation
	:return:
	"""
	success_rate = 0
	targets_original_network = get_leaves_of_tree(simulated_tree)
	correct_classifications = defaultdict(int)
	frequency_of_triplets = defaultdict(int)
	simulated_tree = tree_collapse(simulated_tree)
	for _ in range(0, number_of_trials):

		# Sampling triplets a,b, and c without replacement
		a = random.choice(targets_original_network)
		target_nodes_original_network_copy = list(targets_original_network)
		target_nodes_original_network_copy.remove(a)
		b = random.choice(target_nodes_original_network_copy)
		target_nodes_original_network_copy.remove(b)
		c = random.choice(target_nodes_original_network_copy)

		# Find the triplet pair that is closer together in the simulated tree, to compare to the reconstructed tree
		#a_ancestors = nx.ancestors(simulated_tree, a)
		#b_ancestors = nx.ancestors(simulated_tree, b)
		#c_ancestors = nx.ancestors(simulated_tree, c)
		a_ancestors = [node.split('_')[0] for node in nx.ancestors(simulated_tree, a)]
		b_ancestors = [node.split('_')[0] for node in nx.ancestors(simulated_tree, b)]
		c_ancestors = [node.split('_')[0] for node in nx.ancestors(simulated_tree, c)]
		ab_common = len(set(a_ancestors) & set(b_ancestors))
		ac_common = len(set(a_ancestors) & set(c_ancestors))
		bc_common = len(set(b_ancestors) & set(c_ancestors))
		index = min(ab_common, bc_common, ac_common)

		true_common = '-'
		if ab_common > bc_common and ab_common > ac_common:
			true_common = 'ab'
		elif ac_common > bc_common and ac_common > ab_common:
			true_common = 'ac'
		elif bc_common > ab_common and bc_common > ac_common:
			true_common = 'bc'

		# Find the triplet pair that is closer together in the reconstructed tree, to compare to the simulated tree
		a_ancestors = nx.ancestors(reconstructed_tree, a.split('_')[0])
		b_ancestors = nx.ancestors(reconstructed_tree, b.split('_')[0])
		c_ancestors = nx.ancestors(reconstructed_tree, c.split('_')[0])
		ab_common = len(set(a_ancestors) & set(b_ancestors))
		ac_common = len(set(a_ancestors) & set(c_ancestors))
		bc_common = len(set(b_ancestors) & set(c_ancestors))

		true_common_2 = '-'
		if ab_common > bc_common and ab_common > ac_common:
			true_common_2 = 'ab'
		elif ac_common > bc_common and ac_common > ab_common:
			true_common_2 = 'ac'
		elif bc_common > ab_common and bc_common > ac_common:
			true_common_2 = 'bc'

		correct_classifications[index] += (true_common == true_common_2)
		frequency_of_triplets[index] +=1

		success_rate += (true_common == true_common_2)

	if dict_return:
		return correct_classifications, frequency_of_triplets
	else:
		return success_rate/(1.0 * number_of_trials)