"""Exact three-qubit teleportation simulation. Python standard library only.

Qubit order q0,q1,q2 (most to least significant). Resource:
(1-p)|Phi+><Phi+| + p I4/4. Independent or perfectly linked classical-bit flips.
All gates and quantum measurements ideal. No physical hardware is used.
"""
import cmath
import math

SQRT2 = math.sqrt(2)
STATES = {
    '0': (1, 0), '1': (0, 1),
    '+': (1/SQRT2, 1/SQRT2), '-': (1/SQRT2, -1/SQRT2),
    '+i': (1/SQRT2, 1j/SQRT2), '-i': (1/SQRT2, -1j/SQRT2),
}

def input_state(theta, phi):
    t, f = math.radians(theta), math.radians(phi)
    return (math.cos(t/2), cmath.exp(1j*f)*math.sin(t/2))

def h_gate(v, qubit):
    mask = 1 << (2-qubit)
    out = list(v)
    for i in range(8):
        if not i & mask:
            out[i] = (v[i]+v[i|mask])/SQRT2
            out[i|mask] = (v[i]-v[i|mask])/SQRT2
    return out

def cnot(v, control, target):
    cm, tm = 1 << (2-control), 1 << (2-target)
    out = [0j]*8
    for i, a in enumerate(v):
        out[i ^ tm if i & cm else i] = a
    return out

ERROR_MODELS = ('Independent', 'Linked')

def flip_patterns(e, model):
    """Return (first flip, second flip, probability) for nonzero branches."""
    if model == 'Independent':
        weights = ((1-e)**2, (1-e)*e, e*(1-e), e**2)
    elif model == 'Linked':
        weights = (1-e, 0, 0, e)
    else:
        raise ValueError('Choose Independent or Linked bit errors.')
    return [(mask >> 1, mask & 1, weight) for mask, weight in enumerate(weights) if weight]

def simulate(psi, p=0.0, e=0.0, feedforward=True, model='Independent'):
    if not (0 <= p <= 1 and 0 <= e <= 1):
        raise ValueError('p and e must be between zero and one.')
    if abs(sum(abs(a)**2 for a in psi)-1) > 1e-9:
        raise ValueError('Input state must be normalized.')
    # A convex decomposition of the resource into five pure-state branches.
    resources = [(1-p, (1/SQRT2,0,0,1/SQRT2))]
    resources += [(p/4, tuple(1 if j == k else 0 for j in range(4))) for k in range(4)]
    rho = [[0j,0j],[0j,0j]]
    outcomes = [0.0]*4
    patterns = flip_patterns(e,model)
    for resource_weight, resource in resources:
        if resource_weight == 0:
            continue
        v = [a*b for a in psi for b in resource]
        v = h_gate(cnot(v,0,1),0)
        for m in range(4):
            # Bob's unnormalized conditional vector includes branch probability.
            bob = v[2*m:2*m+2]
            outcomes[m] += resource_weight*sum(abs(a)**2 for a in bob)
            for error0,error1,probability in patterns:
                weight = resource_weight*probability
                b = list(bob)
                if feedforward:
                    m0, m1 = (m >> 1)^error0, (m & 1)^error1
                    if m1:
                        b.reverse()  # X first
                    if m0:
                        b[1] = -b[1]  # then Z
                for i in range(2):
                    for j in range(2):
                        rho[i][j] += weight*b[i]*complex(b[j]).conjugate()
    fidelity = sum(complex(psi[i]).conjugate()*rho[i][j]*psi[j]
                   for i in range(2) for j in range(2)).real
    bloch = (2*rho[0][1].real, -2*rho[0][1].imag, (rho[0][0]-rho[1][1]).real)
    return {'rho':rho, 'fidelity':fidelity, 'outcomes':outcomes, 'bloch':bloch}

def six_state(p,e,feedforward=True,model='Independent'):
    values = {name:simulate(psi,p,e,feedforward,model)['fidelity'] for name,psi in STATES.items()}
    return values, sum(values.values())/6

def prediction(p,e,model='Independent'):
    correct = (1-e)**2 if model == 'Independent' else 1-e
    return (1-p)*(1+2*correct)/3+p/2

