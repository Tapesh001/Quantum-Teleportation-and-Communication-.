import unittest
import random
from backend.engine import STATES, input_state, simulate, six_state, prediction

class Verification(unittest.TestCase):
    def test_linked_errors(self):
        for e in (0,.1,.5,1):
            for p in (0,.2,1):
                values,mean = six_state(p,e,model='Linked')
                # A double flip leaves both Y eigenstates unchanged up to phase.
                for name in STATES:
                    ideal = 1 if name in ('+i','-i') else 1-e
                    self.assertAlmostEqual(values[name],(1-p)*ideal+p/2)
                self.assertAlmostEqual(mean,prediction(p,e,'Linked'))
                self.assertAlmostEqual(six_state(p,e,False,'Linked')[1],.5)

    def test_random_states_ideal_and_no_feedforward(self):
        rng = random.Random(2026)
        for _ in range(80):
            psi = input_state(rng.uniform(0,180),rng.uniform(0,360))
            self.assertAlmostEqual(simulate(psi)['fidelity'],1,places=12)
            r = simulate(psi,rng.random(),rng.random(),False)
            self.assertAlmostEqual(r['fidelity'],.5,places=12)
            self.assertAlmostEqual(r['rho'][0][0].real,.5,places=12)
            self.assertAlmostEqual(abs(r['rho'][0][1]),0,places=12)

    def test_formula_grid(self):
        for p in [0,.2,.4,.6,.8,1]:
            for e in [0,.1,.2,.5,1]:
                self.assertAlmostEqual(six_state(p,e)[1],prediction(p,e),places=12)

    def test_phase_sensitive_inputs(self):
        values, mean = six_state(0,.1)
        for name in ['0','1','+','-']:
            self.assertAlmostEqual(values[name],.9,places=12)
        for name in ['+i','-i']:
            self.assertAlmostEqual(values[name],.82,places=12)
        self.assertAlmostEqual(mean, .8733333333333333,places=12)

    def test_density_matrix_and_outcomes(self):
        for psi in STATES.values():
            r = simulate(psi,.23,.17)
            rho = r['rho']
            self.assertAlmostEqual((rho[0][0]+rho[1][1]).real,1,places=12)
            self.assertAlmostEqual(abs(rho[0][1]-rho[1][0].conjugate()),0,places=12)
            self.assertGreaterEqual((rho[0][0]*rho[1][1]-rho[0][1]*rho[1][0]).real,-1e-12)
            for prob in r['outcomes']:
                self.assertAlmostEqual(prob,.25,places=12)

    def test_complete_noise_and_reported_examples(self):
        for psi in STATES.values():
            self.assertAlmostEqual(simulate(psi,1,.1)['fidelity'],.5,places=12)
        self.assertAlmostEqual(six_state(.2,.1)[1],.7986666666666666,places=12)
        self.assertAlmostEqual(six_state(.6,.1)[1],.6493333333333333,places=12)

