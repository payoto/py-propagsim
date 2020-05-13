from classes import State, Agent, Cell, Transitions, Map
from simulation import split_population, get_durations, get_current_state_durations, get_transitions_ids, evaluate
from simulation import get_cell_positions, get_cell_attractivities, get_cell_unsafeties, get_transitions, get_p_moves
import numpy as np
from time import time
import os, json
from pprint import pprint
from datetime import datetime

CALIBRATION_DIR = os.path.join(*['..', '..', 'calibrations'])
if not os.path.isdir(CALIBRATION_DIR):
    os.makedirs(CALIBRATION_DIR)

# FIXED
DAY = datetime(2020, 4, 20)
N_PERIODS = 14
N_AGENTS = 700000
AVG_AGENTS_HOME = 2.2
N_HOME_CELLS = int(N_AGENTS / AVG_AGENTS_HOME)
PROP_PUBLIC_CELLS = 1 / 70  # there is one public place for 70 people in France
N_CELLS = int(N_HOME_CELLS + N_AGENTS * PROP_PUBLIC_CELLS)
MEAN_HOSP_T = 10 # irrelevant here
MEAN_ICU_T = 18 # irrelevant here
split_pop = split_population(N_AGENTS)
states =  ['healthy', 'asymptomatic', 'asympcont', 'infected', 'hosp', 'icu', 'death', 'recovercont', 'recovered']
states2ids = {state: i for i, state in enumerate(states)}
ids2states = {v: k for k, v in states2ids.items()}



def get_random_parameters():
    pdict = {}
    pdict['n_moves_per_period'] = np.random.choice(np.arange(7, 12)).astype(np.uint16)
    avg_agent_move = np.random.uniform(1, 6)
    pdict['avg_p_move'] = avg_agent_move / pdict['n_moves_per_period']
    pdict['dscale'] = np.random.uniform(15, 50)
    pdict['density_factor'] = np.random.uniform(4, 8)
    pdict['avg_unsafety'] = np.random.uniform(.7, .9)  # scenario where nothing implemented to secure places
    pdict['avg_attractivity'] = np.random.uniform(.2, .8)
    pdict['contagiousity_infected'] = np.random.uniform(.4, 1)
    pdict['contagiousity_asympcont'] = np.random.uniform(0, pdict['contagiousity_infected'] / 2)
    pdict['contagiousity_recovercont'] = np.random.uniform(0, pdict['contagiousity_infected'])
    pdict['mean_infected_t'] = np.random.uniform(4, 10)
    pdict['severity_infected'] = np.random.uniform(.6, .9)  # the value of quarantine time could be kept after
    pdict['severity_recovercont'] = np.random.uniform(0, pdict['severity_infected'])
    pdict['mean_asymptomatic_t'] = np.random.uniform(3.5, 4.5)
    pdict['n_squares_axis'] = int(np.random.uniform(73, 146))
    pdict['prop_cont_factor'] = np.random.uniform(7, 9)
    return pdict


def get_current_state_durations(n_agents, n_asymp=50):
    state_ids, state_durations = np.zeros(n_agents), -1 * np.ones(n_agents)
    inds_asymp = np.random.choice(np.arange(0, n_agents), size=n_asymp, replace=False).astype(np.uint32)
    state_ids[inds_asymp], state_durations[inds_asymp] = 1, 3
    return state_ids.astype(np.uint32), state_durations.astype(np.uint32)


def build_parameters(current_period=0, verbose=0):
    pdict = get_random_parameters()

    state_mm = {'asymptomatic': (pdict['mean_asymptomatic_t'], pdict['mean_asymptomatic_t'] - .2),
                'infected': (pdict['mean_infected_t'], pdict['mean_infected_t'] - 2),
                'asympcont': (1, 1),
                'hosp': (MEAN_HOSP_T, MEAN_HOSP_T - 2),
                'icu': (MEAN_ICU_T, MEAN_ICU_T - 2),
                'recovercont': (2, 1)}

    # vectors
    cell_ids = np.arange(0, N_CELLS).astype(np.uint32)
    attractivities = get_cell_attractivities(N_HOME_CELLS, N_CELLS - N_HOME_CELLS, avg=pdict['avg_attractivity'], p_closed=0)
    unsafeties = get_cell_unsafeties(N_CELLS, N_HOME_CELLS, pdict['avg_unsafety'])
    cell_positions = get_cell_positions(N_CELLS, pdict['n_squares_axis'], pdict['density_factor'])
    xcoords = cell_positions[:,0]
    ycoords = cell_positions[:,1]
    unique_state_ids = np.arange(0, len(states)).astype(np.uint32)
    unique_contagiousities = np.array([0, 0, pdict['contagiousity_asympcont'], pdict['contagiousity_infected'], 0, 0, 0, pdict['contagiousity_recovercont'], 0])
    unique_sensitivities = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0])
    unique_severities = np.array([0, 0, 0, pdict['severity_infected'], 1, 1, 1, pdict['severity_recovercont'], 0])
    transitions = get_transitions(split_pop)
    durations = get_durations(split_pop, state_mm)
    n_agents_generated = durations.shape[0]
    current_state_ids, current_state_durations = get_current_state_durations(n_agents_generated)
    agent_ids = np.arange(0, n_agents_generated).astype(np.uint32)
    home_cell_ids = np.random.choice(np.arange(0, N_HOME_CELLS), size=n_agents_generated).astype(np.uint32)
    p_moves = get_p_moves(n_agents_generated, pdict['avg_p_move'])
    least_state_ids = np.ones(n_agents_generated)  # least severe state is state 1 for all agents


    transitions_ids = get_transitions_ids(split_pop)
    dscale = pdict['dscale']

    array_params = {'cell_ids': cell_ids, 'attractivities': attractivities, 'unsafeties': unsafeties,
                    'xcoords': xcoords, 'ycoords': ycoords, 'unique_state_ids': unique_state_ids,
                    'unique_contagiousities': unique_contagiousities, 'unique_sensitivities': unique_sensitivities,
                    'unique_severities': unique_severities, 'transitions': transitions, 'agent_ids': agent_ids,
                    'home_cell_ids': home_cell_ids, 'p_moves': p_moves, 'least_state_ids': least_state_ids,
                    'current_state_ids': current_state_ids, 'current_state_durations': current_state_durations,
                    'durations': durations, 'transitions_ids': transitions_ids, 'dscale': dscale,
                    'current_period': current_period, 'verbose': verbose}

    return array_params, pdict


def evaluate_move(evaluations):
    ind_start = 6
    evaluations = evaluations[ind_start:]
    n_asymptomatics = []
    for evaluation in evaluations:
        ind_asymptomatic = np.where(evaluation[0] == 1)[0][0].astype(np.uint32)
        n_asymptomatic = evaluation[1][ind_asymptomatic]
        n_asymptomatics.append(n_asymptomatic)
    print(f'DEBUG: n_asymptomatics: {n_asymptomatics}')
    progressions = [(n_asymptomatics[i+1] - n_asymptomatics[i]) / n_asymptomatics[i] for i in range(len(n_asymptomatics) - 1)]
    progressions = np.array(progressions)
    progressions_toget = np.ones(shape=progressions.shape) * .15
    err_pct = np.mean(np.divide(np.abs(np.subtract(progressions_toget, progressions)), progressions_toget)) * 100
    return err_pct, progressions


def run_calibration(n_rounds, current_period=0, verbose=0):
    if not os.path.isdir('../calibrations'):
        os.makedirs('../calibrations')
    memory_error = False
    map = Map()
    best_score = None
    for i in range(n_rounds):
        if i%10 == 0:
            print(f'round {i}...')
        evaluations = []
        array_params, pdict = build_parameters(current_period, verbose)
        try:
            map.from_arrays(**array_params)
        except:
            memory_error = True
            pass
        if memory_error:
            memory_error = False
            continue
            
        for _ in range(N_PERIODS):
            for _ in range(pdict['n_moves_per_period']):
                map.make_move(prop_cont_factor=pdict['prop_cont_factor'])
            map.forward_all_cells()
            state_ids, state_numbers = map.get_states_numbers()
            evaluations.append((state_ids, state_numbers))
        score, progressions = evaluate_move(evaluations)

        if best_score is None or score < best_score:
            fpath = os.path.join(CALIBRATION_DIR, f'move_3e_{i}.npy')
            to_save = {'score': score, 'params': array_params, 'pdict': pdict}
            print(f'New best score found: {score}, saved under {fpath}')
            print(f'Corresponding progressions: {progressions}')
            print(f'corresponding params:')
            pprint(pdict)
            best_score = score
            np.save(fpath, to_save)


run_calibration(n_rounds=1000)