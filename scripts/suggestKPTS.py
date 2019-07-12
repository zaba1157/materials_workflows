#!/usr/bin/env python

#built with python 2.7.6
#transfed to python 3

# Jacob Clary 12/21/2018
# to add:

#script to find kpts using VASP's auto kgrid method

import sys
import numpy as np

def readfile(filename):
    #read a file into a list of strings
    f = open(filename,'r')
    tempfile = f.readlines()
    f.close()
    return tempfile

def read_poscar(path):
    #get elements lists from POSCAR
    pos_tempfile = readfile(path + 'POSCAR')
    pos_tempfile_read = [x.split() for x in pos_tempfile]

    #get lattice
    lattice = pos_tempfile_read[2:5]
    #assumes lattice in angstroms in poscar
    ang2bohr = 1.88973
    lattice = [[float(y)*ang2bohr for y in x] for x in lattice]
    total = sum([int(float(x)) for x in pos_tempfile_read[6]])
    return total,lattice

def reciprocal_lattice(lattice):
    a = lattice[0]
    b = lattice[1]
    c = lattice[2]
    b1 = np.cross(b,c)/(np.dot(a,np.cross(b,c)))
    b2 = np.cross(c,a)/(np.dot(b,np.cross(c,a)))
    b3 = np.cross(a,b)/(np.dot(c,np.cross(a,b)))
    recip_latt = [list(b1),list(b2),list(b3)]
    return recip_latt

def autokgrid(recip_latt,length):
    #generate kgrid using VASP's auto kgrid method
    b1 = recip_latt[0]
    b2 = recip_latt[1]
    b3 = recip_latt[2]
    N1 = max(1,length*np.linalg.norm(b1)+0.5)
    N2 = max(1,length*np.linalg.norm(b2)+0.5)
    N3 = max(1,length*np.linalg.norm(b3)+0.5)
    return int(N1),int(N2),int(N3)

kmin = sys.argv[1]          #set this as variable or via argparse
indir = './'    
total,lattice = read_poscar(indir)
kmin = float(kmin)/total
#generates kpts same as vasp
recip_latt = reciprocal_lattice(lattice)
Nk = 0
L = 5
kaold = 0
kbold = 0
kcold = 0
while Nk < kmin:
    ka,kb,kc = autokgrid(recip_latt,L)
    Nk = ka*kb*kc
    L += 2
    kaold = ka
    kbold = kb
    kcold = kc
print(str(ka), str(kb), str(kc))            
kptstr = str(ka) + ' ' + str(kb) + ' ' + str(kc) + '\n'
file = open('KPOINTS','w')
file.write('Kpoints file created using kpointsuggest.py\n')
file.write(str(0)+'\n')
file.write('Gamma\n')
file.write(kptstr)
file.close()
