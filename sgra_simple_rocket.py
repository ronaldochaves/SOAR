# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 15:33:27 2016

@author: levi
"""

# a file for solving rocket single stage to orbit with L=0 and D=0


import numpy
import datetime
import matplotlib.pyplot as plt

from scipy.integrate import odeint
from numpy.linalg import norm
from utils import interpV, interpM, ddt
from prob_rocket_sgra import declProb, calcPhi, calcPsi, calcGrads, plotSol

#from scipy.integrate import quad

# ##################
# SOLUTION DOMAIN:
# ##################

def calcLamDotGrad(lam,t,tVec,fxInv,phixInv):
    fxt = interpV(t,tVec,fxInv)
    phixt = interpM(t,tVec,phixInv)

    return phixt.dot(lam) - fxt

def calcLamDotRest(lam,t,tVec,phixInv):
    phixt = interpM(t,tVec,phixInv)
    return phixt.dot(lam)

def calcADotGrad(A,t,tVec,phixVec,phiuVec,phipVec,B,C):
    #print("In calcADot!")
    phixt = interpM(t,tVec,phixVec)
    phiut = interpM(t,tVec,phiuVec)
    phipt = interpM(t,tVec,phipVec)
    Bt = interpV(t,tVec,B)

    #print('phixt =',phixt)
    #print('phiut =',phiut)
    #print('Bt =',Bt)

    return phixt.dot(A) + phiut.dot(Bt) + phipt.dot(C)

def calcADotRest(A,t,tVec,phixVec,phiuVec,phipVec,B,C,aux):
    #print("In calcADot!")
    phixt = interpM(t,tVec,phixVec)
    phiut = interpM(t,tVec,phiuVec)
    phipt = interpM(t,tVec,phipVec)
    auxt = interpV(t,tVec,aux)
    Bt = interpV(t,tVec,B)
    #print('phixt =',phixt)
    #print('phiut =',phiut)
    #print('Bt =',Bt)

    return phixt.dot(A) + phiut.dot(Bt) + phipt.dot(C) + auxt

def calcP(sizes,x,u,pi,constants,boundary,restrictions):
    print("\nIn calcP.")
    N = sizes['N']

    dt = 1.0/(N-1)

    phi = calcPhi(sizes,x,u,pi,constants,restrictions)
    psi = calcPsi(sizes,x,boundary)
    dx = ddt(sizes,x)
    vetP = numpy.empty(N)
    vetIP = numpy.empty(N)
    P = 0.0
    P += .5*norm(dx[0,:]-phi[0,:])**2
    vetP[0] = .5*norm(dx[0,:]-phi[0,:])**2
    vetIP[0] = P

    for t in range(1,N-1):
        vetP[t] = norm(dx[t,:]-phi[t,:])**2
        P += norm(dx[t,:]-phi[t,:])**2
        vetIP[t] = P

    P += .5*norm(dx[N-1,:]-phi[N-1,:])**2
    vetP[N-1] = .5*norm(dx[N-1,:]-phi[N-1,:])**2
    vetIP[N-1] = P

    P *= dt
    vetP *= dt
    vetIP *= dt

    tInutil = numpy.arange(0,1.0+dt,dt)

    plt.plot(tInutil,vetP)
    plt.grid(True)
    plt.title("Integrand of P")
    plt.show()

    plt.plot(tInutil,vetIP)
    plt.grid(True)
    plt.title("Partially integrated P")
    plt.show()


    Ppsi = norm(psi)
    print("P_int = {:.4E}".format(P)+", P_psi = {:.4E}".format(Ppsi))
    P += Ppsi
    return P

def calcQ(sizes,x,u,pi,lam,mu,constants,restrictions):
    # Q expression from (15)

    N = sizes['N']
    p = sizes['p']
    dt = 1.0/(N-1)

    # get gradients
    Grads = calcGrads(sizes,x,u,pi,constants,restrictions)
    phix = Grads['phix']
    phiu = Grads['phiu']
    phip = Grads['phip']
    fx = Grads['fx']
    fu = Grads['fu']
    fp = Grads['fp']
    psix = Grads['psix']
    #psip = Grads['psip']
    dlam = ddt(sizes,lam)
    Qx = 0.0
    Qu = 0.0
    Qp = 0.0
    Qt = 0.0
    Q = 0.0
    auxVecIntQ = numpy.zeros(p)
    isnan = 0
    for k in range(1,N-1):
#        dlam[k,:] = lam[k,:]-lam[k-1,:]
        Qx += norm(dlam[k,:] - fx[k,:] + phix[k,:,:].transpose().dot(lam[k,:]))**2
        Qu += norm(fu[k,:]-phiu[k,:,:].transpose().dot(lam[k,:]))**2
        auxVecIntQ += fp[k,:] - phip[k,:,:].transpose().dot(lam[k,:])
        if numpy.math.isnan(Qx) or numpy.math.isnan(Qu):
            isnan+=1
            if isnan == 1:
                print("k_nan=",k)
   #
    Qx += .5*(norm(dlam[0,:] - fx[0,:] + phix[0,:,:].transpose().dot(lam[0,:]))**2)
    Qx += .5*(norm(dlam[N-1,:] - fx[N-1,:] + phix[N-1,:,:].transpose().dot(lam[N-1,:]))**2)

    Qu += .5*norm(fu[0,:]-phiu[0,:,:].transpose().dot(lam[0,:]))**2
    Qu += .5*norm(fu[N-1,:]-phiu[N-1,:,:].transpose().dot(lam[N-1,:]))**2

    Qx *= dt
    Qu *= dt

    auxVecIntQ += .5*(fp[0,:] - phip[0,:,:].transpose().dot(lam[0,:]))
    auxVecIntQ += .5*(fp[N-1,:] - phip[N-1,:,:].transpose().dot(lam[N-1,:]))

    auxVecIntQ *= dt
    Qp = norm(auxVecIntQ)
    Qt = norm(lam[N-1,:] + psix.transpose().dot(mu))
#"Qx =",Qx)

    Q = Qx + Qu + Qp + Qt
    print("Q = {:.4E}".format(Q)+": Qx = {:.4E}".format(Qx)+", Qu = {:.4E}".format(Qu)+", Qp = {:.4E}".format(Qp)+", Qt = {:.4E}".format(Qt))

    return Q

def calcStepGrad(x,u,pi,lam,mu,A,B,C,restrictions):

#    alfa = 1.0
#    nx = x + alfa * A
#    nu = u + alfa * B
#    np = pi + alfa * C
#
#    Q0 = calcQ(sizes,nx,nu,np,lam,mu)
#    print("Q =",Q0)
#
#    Q = Q0
#    alfa = .8
#    nx = x + alfa * A
#    nu = u + alfa * B
#    np = pi + alfa * C
#    nQ = calcQ(sizes,nx,nu,np,lam,mu)
#    cont = 0
#    while (nQ-Q)/Q < -.05 and alfa > 1.0e-11 and cont < 5:
#        cont += 1
#        Q = nQ
#        alfa *= .5
#        nx = x + alfa * A
#        nu = u + alfa * B
#        np = pi + alfa * C
#        nQ = calcQ(sizes,nx,nu,np,lam,mu)
#        print("alfa =",alfa,"Q =",nQ)
#
#    if Q>Q0:
#        alfa = 1.0

    # "Trissection" method
    alfa = 1.0
    nx = x + alfa * A
    nu = u + alfa * B
    np = pi + alfa * C

    oldQ = calcQ(sizes,nx,nu,np,lam,mu,constants,restrictions)
    nQ = .9*oldQ
#    print("Q =",Q)
    alfaMin = 0.0
    alfaMax = 1.0
    cont = 0
    while (nQ-oldQ)/oldQ < -.05 and cont < 5:
        oldQ = nQ

        dalfa = (alfaMax-alfaMin)/3.0
        alfaList = numpy.array([alfaMin,alfaMin+dalfa,alfaMax-dalfa,alfaMax])
        QList = numpy.empty(numpy.shape(alfaList))

        for j in range(4):
            alfa = alfaList[j]

            nx = x + alfa * A
            nu = u + alfa * B
            np = pi + alfa * C

            Q = calcQ(sizes,nx,nu,np,lam,mu,constants,restrictions)
            QList[j] = Q
        #
        print("QList:",QList)
        minQ = QList[0]
        indxMinQ = 0

        for j in range(1,4):
            if QList[j] < minQ:
                indxMinQ = j
                minQ = QList[j]
        #

        alfa = alfaList[indxMinQ]
        nQ = QList[indxMinQ]
        print("nQ =",nQ)
        if indxMinQ == 0:
            alfaMin = alfaList[0]
            alfaMax = alfaList[1]
        elif indxMinQ == 1:
            if QList[0] < QList[2]:
                alfaMin = alfaList[0]
                alfaMax = alfaList[1]
            else:
                alfaMin = alfaList[1]
                alfaMax = alfaList[2]
        elif indxMinQ == 2:
            if QList[1] < QList[3]:
                alfaMin = alfaList[1]
                alfaMax = alfaList[2]
            else:
                alfaMin = alfaList[2]
                alfaMax = alfaList[3]
        elif indxMinQ == 3:
            alfaMin = alfaList[2]
            alfaMax = alfaList[3]

        cont+=1
    #

    return .5*(alfaMin+alfaMax)

def grad(sizes,x,u,pi,t,Q0,restrictions):
    print("In grad.")

    print("Q0 =",Q0)
    # get sizes
    N = sizes['N']
    n = sizes['n']
    m = sizes['m']
    p = sizes['p']
    q = sizes['q']

    # get gradients
    Grads = calcGrads(sizes,x,u,pi,constants,restrictions)

    phix = Grads['phix']
    phiu = Grads['phiu']
    phip = Grads['phip']
    fx = Grads['fx']
    fu = Grads['fu']
    fp = Grads['fp']
    psix = Grads['psix']
    psip = Grads['psip']
    dt = Grads['dt']

    # prepare time reversed/transposed versions of the arrays
    psixTr = psix.transpose()
    fxInv = fx.copy()
    phixInv = phix.copy()
    phiuTr = numpy.empty((N,m,n))
    phipTr = numpy.empty((N,p,n))
    for k in range(N):
        fxInv[k,:] = fx[N-k-1,:]
        phixInv[k,:,:] = phix[N-k-1,:,:].transpose()
        phiuTr[k,:,:] = phiu[k,:,:].transpose()
        phipTr[k,:,:] = phip[k,:,:].transpose()
    psipTr = psip.transpose()

    # Prepare array mu and arrays for linear combinations of A,B,C,lam
    mu = numpy.zeros(q)
    M = numpy.ones((q+1,q+1))

    arrayA = numpy.empty((q+1,N,n))
    arrayB = numpy.empty((q+1,N,m))
    arrayC = numpy.empty((q+1,p))
    arrayL = arrayA.copy()
    arrayM = numpy.empty((q+1,q))

    for i in range(q+1):
        mu = 0.0*mu
        if i<q:
            mu[i] = 1.0

        #print("mu =",mu)
        # integrate equation (38) backwards for lambda
        auxLamInit = - psixTr.dot(mu)
        auxLam = odeint(calcLamDotGrad,auxLamInit,t,args=(t,fxInv, phixInv))

        # Calculate B
        B = -fu
        lam = auxLam.copy()
        for k in range(N):
            lam[k,:] = auxLam[N-k-1,:]
            B[k,:] += phiuTr[k,:,:].dot(lam[k,:])

        # Calculate C
        C = numpy.zeros(p)
        for k in range(1,N-1):
            C += fp[k,:] - phipTr[k,:,:].dot(lam[k,:])
        C += .5*(fp[0,:] - phipTr[0,:,:].dot(lam[0,:]))
        C += .5*(fp[N-1,:] - phipTr[N-1,:,:].dot(lam[N-1,:]))
        C *= -dt
        C -= -psipTr.dot(mu)

#        plt.plot(t,B)
#        plt.grid(True)
#        plt.xlabel("t")
#        plt.ylabel("B")
#        plt.show()
#
        # integrate diff equation for A
        A = odeint(calcADotGrad,numpy.zeros(n),t, args=(t,phix,phiu,phip,B,C))

#        plt.plot(t,A)
#        plt.grid(True)
#        plt.xlabel("t")
#        plt.ylabel("A")
#        plt.show()

        arrayA[i,:,:] = A
        arrayB[i,:,:] = B
        arrayC[i,:] = C
        arrayL[i,:,:] = lam
        arrayM[i,:] = mu
        M[1:,i] = psix.dot(A[N-1,:]) + psip.dot(C)
    #

    # Calculations of weights k:

    col = numpy.zeros(q+1)
    col[0] = 1.0
    K = numpy.linalg.solve(M,col)
    print("K =",K)

    # summing up linear combinations
    A = 0.0*A
    B = 0.0*B
    C = 0.0*C
    lam = 0.0*lam
    mu = 0.0*mu
    for i in range(q+1):
        A += K[i]*arrayA[i,:,:]
        B += K[i]*arrayB[i,:,:]
        C += K[i]*arrayC[i,:]
        lam += K[i]*arrayL[i,:,:]
        mu += K[i]*arrayM[i,:]

    # Calculation of alfa
    alfa = calcStepGrad(x,u,pi,lam,mu,A,B,C,restrictions)

    nx = x + alfa * A
    nu = u + alfa * B
    np = pi + alfa * C
    Q = calcQ(sizes,nx,nu,np,lam,mu,restrictions)

    print("Leaving grad with alfa =",alfa)

    return nx,nu,np,lam,mu,Q

def calcStepRest(t,x,u,pi,A,B,C,constants,boundary,restrictions):

    P0 = calcP(sizes,x,u,pi,constants,boundary,restrictions)
    
    alfa = 1.0
    nx = x + alfa * A
    nu = u + alfa * B
    np = pi + alfa * C
    P1 = calcP(sizes,nx,nu,np,constants,boundary,restrictions)
    print("For alfa = 1, P = {:.4E}".format(P1))

    P = P1
    alfa = .8
    nx = x + alfa * A
    nu = u + alfa * B
    np = pi + alfa * C
    nP = calcP(sizes,nx,nu,np,constants,boundary,restrictions)

    cont = 0; keepSearch = True
    while keepSearch: #(nP-P)/P < -.05 or P > P0: #alfa > 1.0e-11 and cont < 15:
        cont += 1
        P = nP
        alfa *= .5
        nx = x + alfa * A
        nu = u + alfa * B
        np = pi + alfa * C
        nP = calcP(sizes,nx,nu,np,constants,boundary,restrictions)

        plotSol(sizes,t,nx,nu,np,constants,restrictions)
        print("alfa =",alfa,", P = {:.4E}".format(nP)," (P0 = {:.4E})".format(P0))
        if nP < P0:
            keepSearch = (nP-P)/P < -.05 and alfa > 1.0e-11

    return alfa

def rest(sizes,x,u,pi,t,constants,boundary,restrictions):
    print("\nIn rest.")

    P0 = calcP(sizes,x,u,pi,constants,boundary,restrictions)
    print("P0 = {:.4E}".format(P0))

    # get sizes
    N = sizes['N']
    n = sizes['n']
    m = sizes['m']
    p = sizes['p']
    q = sizes['q']

    print("Calc phi...")
    # calculate phi and psi
    phi = calcPhi(sizes,x,u,pi,constants,restrictions)
    print("Calc psi...")
    psi = calcPsi(sizes,x,boundary)

    # aux: phi - dx/dt
    aux = phi.copy()
    aux -= ddt(sizes,x)

    # get gradients
    print("Calc grads...")
    Grads = calcGrads(sizes,x,u,pi,constants,restrictions)

    dt = Grads['dt']
    phix = Grads['phix']
    phiu = Grads['phiu']
    phip = Grads['phip']
    fx = Grads['fx']
    psix = Grads['psix']
    psip = Grads['psip']

    print("Preparing matrices...")
    psixTr = psix.transpose()
    fxInv = fx.copy()
    phixInv = phix.copy()
    phiuTr = numpy.empty((N,m,n))
    phipTr = numpy.empty((N,p,n))
    psipTr = psip.transpose()

    for k in range(N):
        fxInv[k,:] = fx[N-k-1,:]
        phixInv[k,:,:] = phix[N-k-1,:,:].transpose()
        phiuTr[k,:,:] = phiu[k,:,:].transpose()
        phipTr[k,:,:] = phip[k,:,:].transpose()

    mu = numpy.zeros(q)

    # Matrix for linear system involving k's
    M = numpy.ones((q+1,q+1))

    # column vector for linear system involving k's    [eqs (88-89)]
    col = numpy.zeros(q+1)
    col[0] = 1.0 # eq (88)
    col[1:] = -psi # eq (89)

    arrayA = numpy.empty((q+1,N,n))
    arrayB = numpy.empty((q+1,N,m))
    arrayC = numpy.empty((q+1,p))
    arrayL = arrayA.copy()
    arrayM = numpy.empty((q+1,q))

    opt = dict()

    print("Beginning loop for solutions...")
    for i in range(q+1):
        mu = 0.0*mu
        if i<q:
            mu[i] = 1.0

        # integrate equation (75-2) backwards
        auxLamInit = - psixTr.dot(mu)
        auxLam = odeint(calcLamDotRest,auxLamInit,t,args=(t,phixInv))

        # equation for Bi (75-3)
        B = numpy.empty((N,m))
        lam = auxLam.copy()
        for k in range(N):
            lam[k,:] = auxLam[N-k-1,:]
            B[k,:] = phiuTr[k,:,:].dot(lam[k,:])
        
        while B.max() > numpy.pi or B.min() < - numpy.pi:
            lam *= .1
            mu *= .1
            B *= .1
            print("mu =",mu)
        
        # equation for Ci (75-4)
        C = numpy.zeros(p)
        for k in range(1,N-1):
            C += phipTr[k,:,:].dot(lam[k,:])
        C += .5*(phipTr[0,:,:].dot(lam[0,:]))
        C += .5*(phipTr[N-1,:,:].dot(lam[N-1,:]))
        C *= dt
        C -= -psipTr.dot(mu)

        opt['mode'] = 'states:Lambda'
        plotSol(sizes,t,lam,B,C,constants,restrictions,opt)

        print("Integrating ODE for A [i = "+str(i)+"] ...")
        # integrate equation for A:
        A = odeint(calcADotRest,numpy.zeros(n),t,args= (t,phix,phiu,phip,B,C,aux))
        
        # store solution in arrays
        arrayA[i,:,:] = A
        arrayB[i,:,:] = B
        arrayC[i,:] = C
        arrayL[i,:,:] = lam
        arrayM[i,:] = mu
        
        opt['mode'] = 'var'
        plotSol(sizes,t,A,B,C,constants,restrictions,opt)
        
        # Matrix for linear system (89)
        M[1:,i] = psix.dot(A[N-1,:]) + psip.dot(C)
        #M[1:,i] += psip.dot(C)#psip * C
    #

    # Calculations of weights k:

    K = numpy.linalg.solve(M,col)
    print("K =",K)

    # summing up linear combinations
    A = 0.0*A
    B = 0.0*B
    C = 0.0*C
    lam = 0.0*lam
    mu = 0.0*mu
    for i in range(q+1):
        A += K[i]*arrayA[i,:,:]
        B += K[i]*arrayB[i,:,:]
        C += K[i]*arrayC[i,:]
        lam += K[i]*arrayL[i,:,:]
        mu += K[i]*arrayM[i,:]

    optPlot = dict()
    optPlot['mode'] = 'var'
    plotSol(sizes,t,A,B,C,constants,restrictions,optPlot)

    print("Calculating step...")
    alfa = calcStepRest(t,x,u,pi,A,B,C,constants,boundary,restrictions)
    nx = x + alfa * A
    nu = u + alfa * B
    np = pi + alfa * C

    print("Leaving rest with alfa =",alfa)
    return nx,nu,np,lam,mu

# ##################
# MAIN SEGMENT:
# ##################
if __name__ == "__main__":
    print('--------------------------------------------------------------------------------')
    print('\nThis is SGRA_SIMPLE_ROCKET.py!')
    print(datetime.datetime.now())
    
    opt = dict()
    opt['initMode'] = 'extSol'#'default'#'extSol'

    # declare problem:
    sizes,t,x,u,pi,lam,mu,tol,constants,boundary,restrictions = declProb(opt)

    Grads = calcGrads(sizes,x,u,pi,constants,restrictions)
    phi = calcPhi(sizes,x,u,pi,constants,restrictions)
    psi = calcPsi(sizes,x,boundary)
#    phix = Grads['phix']
#    phiu = Grads['phiu']
#    psix = Grads['psix']
#    psip = Grads['psip']

    print("\nProposed initial guess:")

    P = calcP(sizes,x,u,pi,constants,boundary,restrictions)
    Q = calcQ(sizes,x,u,pi,lam,mu,constants,restrictions)
    optPlot = dict()
    optPlot['P'] = P
    optPlot['Q'] = Q
    optPlot['mode'] = 'sol'
    optPlot['dispP'] = True
    optPlot['dispQ'] = False

    plotSol(sizes,t,x,u,pi,constants,restrictions,optPlot)

    tolP = tol['P']
    tolQ = tol['Q']

    MaxIterRest = 10000
    histP = numpy.zeros(MaxIterRest)
    uman = numpy.linspace(0,MaxIterRest,MaxIterRest+1)

    # first restoration rounds:
    NIterRest = 0
    histP[0] = P
    while P > tolP and NIterRest < MaxIterRest:
        NIterRest += 1
        x,u,pi,lam,mu = rest(sizes,x,u,pi,t,constants,boundary,restrictions)
        P = calcP(sizes,x,u,pi,constants,boundary,restrictions)
        optPlot['P'] = P
        histP[NIterRest] = P
        plotSol(sizes,t,x,u,pi,constants,restrictions,optPlot)

        plt.plot(uman[0:(NIterRest+1)],histP[0:(NIterRest+1)],'o')
        plt.grid()
        plt.title("Convergence of P")
        plt.ylabel("P")
        plt.xlabel("Iterations")
        plt.show()
        
        print("\a")
        input("So far, so good?")

    print("\nAfter first rounds of restoration:")
    Q = calcQ(sizes,x,u,pi,lam,mu,constants,restrictions)
    optPlot['Q'] = Q; optPlot['dispQ'] = True
    plotSol(sizes,t,x,u,pi,constants,restrictions,optPlot)

    # Gradient rounds:
    while Q > tolQ:
        while P > tolP:
            x,u,pi,lam,mu = rest(sizes,x,u,pi,t,constants,boundary,restrictions)
            P = calcP(sizes,x,u,pi,constants,boundary,restrictions)
            optPlot['P'] = P
            plotSol(sizes,t,x,u,pi,constants,restrictions, optPlot)
        #
        x,u,pi,lam,mu,Q = grad(sizes,x,u,pi,t,Q,restrictions)
        optPlot['Q'] = Q
        plotSol(sizes,t,x,u,pi,constants,restrictions,optPlot)
    #
#
