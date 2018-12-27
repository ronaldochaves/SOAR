#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  2 22:49:46 2018

@author: levi

This is a module for simple integration of the rocket equations,
in order to yield a basic (naive) initial guess for MSGRA.
"""

import numpy
from interf import logger

# TODO: there will be a conflict when this module gets imported in
#  probRock.py, because this module already loads probRock (mainly for
#  using plotSol, I hope calcXDot can be imported separately, so there is
#  no conflict with it.) Anyway, we will probably have to make another
#  version of plotSol to it.
import probRock

def speed_ang_controller(v,gama,M,pars):
    #print("\nIn speed_ang_controller!")
    #print(pars)
    #print(v)

    vOrb, gOrb, rOrb = pars['vOrb'], pars['gOrb'], pars['rOrb']
    lv, lg = pars['lv'], pars['lg']

    dv,dg = v-vOrb, gama

    # Calculate nominal thrust to weight ratio
    psi = - lv * dv / gOrb + dg

    # perform saturations
    if psi < 0.:
        psi = 0.
    Thr = psi * M * gOrb
    if Thr > pars['Thrust']:
        Thr = pars['Thrust']

    beta = Thr / pars['Thrust']
    psi = Thr / M / gOrb

    # calculate nominal angle of attack
    alfa = -(vOrb/gOrb/psi) * (lg * dg + 2. * dv / rOrb)

    # perform saturations
    if alfa > pars['alfa']:
        alfa = pars['alfa']
    elif alfa < -pars['alfa']:
        alfa = -pars['alfa']

    return alfa, beta


# TODO: 'objectify' this module. It would be great for development and
#  testing if the trajectory guess could be generated in here as well,
#  instead of having to run main.py every time.

# TODO: make a module for loading parameters from .its file. Probably just
#  loading some of itsme.py's methods does the trick.

def naivGues():

    d2r = numpy.pi/180.0
    m, n, s = 2, 4, 3
    p = s
    addArcs = 2
    q = (n+n-1) + n * (s-addArcs-1) + (n+1) * addArcs

    ones = numpy.ones(s)
    constants = {'r_e': 6371.0,
                 'GM': 398600.4415,
                 'Thrust': 100. * ones,
                 's_ref': 0.7853981633974482e-06 * ones,
                 's_f': 0.1 * ones,
                 'Isp': 450. * ones,
                 'CL0': 0. * ones,#-0.02]),
                 'CL1': .8 * ones,
                 'CD0': .05 * ones,
                 'CD2': .5 * ones,
                 'DampCent': -30.,
                 'DampSlop': 10.,
                 'Kpf': 0.,
                 'PFmode': 'tanh'}
    constants['grav_e'] = constants['GM']/(constants['r_e']**2)

    h_final = 473.
    V_final = numpy.sqrt(constants['GM']/(constants['r_e']+h_final))
    missDv = numpy.sqrt((constants['GM']/constants['r_e']) *
                        (2.0-1./(1.+h_final/constants['r_e'])))
    boundary = {'h_initial': 0.,#0.,
                'V_initial': 1e-6,#.05,#
                'gamma_initial': 90. * d2r,#5*numpy.pi,
                'm_initial': 3000,
                'h_final': h_final,
                'V_final': V_final,
                'gamma_final': 0.,
                'mission_dv': missDv}

    alfa_max = 3. * numpy.pi / 180.
    restrictions = {'alpha_min': -alfa_max,
                    'alpha_max': alfa_max,
                    'beta_min': 0.,
                    'beta_max': 1.,
                    'acc_max': 4. * constants['grav_e'],
                    # Remove this once the loading from file is ready!
                    'pi_min': numpy.zeros(p),
                    'pi_max': [None]*p}
    # 'TargHeig': TargHeig}

    # Declare a running solution
    sol = probRock.prob()
    # Open a logger object, just for printing
    sol.log = logger(sol.probName)#,mode='screen')

    sol.constants = constants
    # Anything, really, it is just because there should be a mPayl attribute
    sol.mPayl = 10.
    # This is necessary for calculating Psi at the end:
    sol.addArcs = addArcs
    sol.isStagSep = numpy.array([False]*s)

    sol.boundary = boundary
    sol.restrictions = restrictions
    sol.initMode = 'extSol'
    # Show the parameters before integration
    sol.printPars()
    #input("\nIAE?")

    # Maximum dimensional time for any arc [s]
    tf = 1000.
    # Dimensional dt for integration [s]
    dtd = 0.1
    Nmax = int(tf/dtd)+1

    # base thrust to weight ratio
    psi = 1.7

    h, V = boundary['h_initial'], boundary['V_initial']
    gama, M =  boundary['gamma_initial'], boundary['m_initial']
    # running x
    x_ = numpy.array([h, V, gama, M])
    # prepare arrays for integration
    x, u = numpy.zeros((Nmax,n,s)), numpy.empty((Nmax,m,s))
    pi = numpy.empty(s)
    # initial condition, first arc
    x[0,:,0] = x_

    # Dimensional running time
    td = 0.
    finlElem = numpy.zeros(s,dtype='int')
    sol.log.printL("\nProceeding for naive integrations...")
    for arc in range(s):
        tdArc = 0. # dimensional running time for this arc
        tStart = 0.
        if arc == 0:
            # First arc:
            # - rise vertically
            # - at full thrust
            # - until v = 100 m/s
            #alfaFun = lambda t, state: 0.
            #numpy.arcsin((g / V - V / r) * numpy.cos(gama) * (M * V / Thr)
            #betaFun = lambda t, state: 1.
            ctrl = lambda t, state: [0., 1.]
            arcCond = lambda t, state: state[1] < 0.1
        elif arc == 1:
            # Second arc:
            # - maximum turning (half of max ang of attack)
            # - constant specific thrust
            # - until gamma = 10deg
            #alfaFun = lambda t, state: -2. * min([1., ((t-tStart)/ 10.]) * d2r
            #alfaFun = lambda t, state: -2. * d2r
            #betaFun = lambda t, state: min([psi * state[3] * \
            #                               constants['grav_e'] / \
            #                               constants['Thrust'][1], 1.])
            #betaFun = lambda t, state: psi * state[3] * \
            #                            constants['grav_e'] / \
            #                            constants['Thrust'][1]
            ctrl = lambda t, state: [-.6 * d2r,
                                     min([psi * state[3] * \
                                          constants['grav_e'] / \
                                          constants['Thrust'][1], 1.])]
            arcCond = lambda t, state: state[2] > 5. * d2r
        elif arc == 2:
            pars = {'rOrb': constants['r_e'] + boundary['h_final'],
                    'vOrb': boundary['V_final'],
                    'lv': .01,
                    'lg': .1,
                    'Thrust': constants['Thrust'][2],
                    'alfa': restrictions['alpha_max']}
            pars['gOrb'] = constants['GM'] / (pars['rOrb']**2)
            ctrl = lambda t, state: speed_ang_controller(state[1],state[2],
                                                         state[3],pars)
            tolV, tolG = 0.01, 0.1 * d2r
            arcCond = lambda t, state: abs(state[1]-pars['vOrb']) > tolV or \
                                        (abs(state[2]) > tolG)
        else:
            raise(Exception("Undefined controls for arc = {}.".format(arc)))
        #(-2.*(1.-td/tf)-1.*(td/tf))*d2r#numpy.arcsin((g/V - V/r)*numpy.cos(gama) * (M*V/Thr) )

        # RK4 integration
        k = 1; dtd2, dtd6 = dtd/2., dtd/6.
        while k < Nmax and arcCond(td, x_):
            #u_ = numpy.array([alfaFun(td,x_),betaFun(td,x_)])
            u_ = ctrl(td, x_)
            # first derivative
            f1 = probRock.calcXdot(td, x_, u_, constants, arc)
            tdpm = td + dtd2
            # x at half step, with f1
            x2 = x_ + dtd2 * f1
            # u at half step, with f1
            #u2 = numpy.array([alfaFun(tdpm, x2), betaFun(tdpm, x2)])
            u2 = ctrl(tdpm, x2)
            # second derivative
            f2 = probRock.calcXdot(tdpm, x2, u2, constants, arc)
            # x at half step, with f2
            x3 = x_ + dtd2 * f2  # x at half step, with f2
            # u at half step, with f2
            #u3 = numpy.array([alfaFun(tdpm, x3), betaFun(tdpm, x3)])
            u3 = ctrl(tdpm, x3)
            # third derivative
            f3 = probRock.calcXdot(tdpm, x3, u3, constants, arc)
            td4 = td + dtd
            # x at half step, with f3
            x4 = x_ + dtd * f3  # x at next step, with f3
            # u at half step, with f3
            u4 = ctrl(td4, x4)
            # fourth derivative
            f4 = probRock.calcXdot(td4, x4, u4, constants, arc)
            # update state with all four derivatives f1, f2, f3, f4
            x_ += dtd6 * (f1 + f2 + f2 + f3 + f3 + f4)

            # update dimensional time
            td = td4
            # store states and controls
            x[k,:,arc], u[k-1,:,arc] = x_, u_
            k += 1
        # Store the final time index for this arc
        finlElem[arc] = k
        # avoiding nonsense values for controls in the last time of the arc
        u[-1, :, arc] = u[-2,:,arc]
        # continuity condition for next arc (if it exists)
        if arc < s-1:
            x[0,:,arc+1] = x[k-1,:,arc]
        # Store time into pi array
        pi[arc] = td
    sol.log.printL("... naive integrations are complete.")

    # Load constants into sol object
    sol.N = int(max(finlElem))
    sol.log.printL("Original N: {}".format(sol.N))
    # This line is for redefining N, if so,
    # while still keeping the 100k + 1 "structure"
    sol.N = 1*(Nmax-1) + 1
    sol.log.printL("New N: {}".format(sol.N))
    sol.m, sol.n, sol.p, sol.q, sol.s = m, n, s, q, s
    sol.dt = 1./(sol.N-1)
    sol.t = numpy.linspace(0.,1.,num=sol.N)
    sol.Ns = 2 * n * s + sol.p
    # Perform interpolations to keep every arc with the same refinement
    xFine, uFine = numpy.empty((sol.N,n,s)), numpy.empty((sol.N,m,s))
    sol.log.printL("\nProceeding to interpolations...")
    for arc in range(s):
        # "Fine" time array
        tFine = sol.t * pi[arc]
        # "Coarse" time array
        tCoar = numpy.linspace(0.,pi[arc],num=finlElem[arc])

        # perform the actual interpolations
        for stt in range(n):
            xFine[:,stt,arc] = numpy.interp(tFine,tCoar,
                                            x[:finlElem[arc],stt,arc])
        for ctr in range(m):
            uFine[:,ctr,arc] = numpy.interp(tFine,tCoar,
                                            u[:finlElem[arc],ctr,arc])
    sol.log.printL("... interpolations complete.")
    # Load interpolated solutions into sol object
    sol.x = xFine
    # Control is stored non-dimensionally
    sol.u = sol.calcAdimCtrl(uFine[:,0,:],uFine[:,1,:])
    sol.pi = pi
    # This is just for compatibility. Current probRock formulation demands
    # a target height array for the first "artificial" arcs
    sol.boundary['TargHeig'] = numpy.array(sol.x[-1,0,:])
    # These arrays get zeros, although that does not make much sense
    sol.lam = numpy.zeros_like(sol.x,dtype='float')
    sol.mu = numpy.zeros(q)
    sol.log.printL("\nNaive solution is ready, returning now!")
    return sol


if __name__ == "__main__":
    # Generate the initial guess
    sol = naivGues()

    # Plot solution
    sol.plotSol() # normal
    # non-dimensional time to check better the details in short arcs
    sol.plotSol(piIsTime=False)
    # Plot trajectory
    sol.plotTraj()
    # sol.plotTraj(fullOrbt=True,mustSaveFig=False)
    sol.log.printL("\nFinal error on boundaries:\n"+str(sol.calcPsi()))

    # TESTING the obtained solution with rest
    contRest = 0
    while sol.P > sol.tol['P']:
        sol.rest()
        contRest += 1
        sol.plotSol()
        # input("\nOne more restoration complete.")
    #

    sol.showHistP()