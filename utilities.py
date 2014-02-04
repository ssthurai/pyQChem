# pyQchem - Input/Output-Tools for Q-Chem
# Copyright (C) 2014  Andreas W. Hauser

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#####################################################################
#                                                                   #
#                 pyQchem - Tools and Subroutines                   #
#                                                                   #
#####################################################################

# This file contains a few hidden methods for easy file reading,
# one reading method for each type of fragment.


######################### STANDARD MODULES ##########################

from copy import deepcopy
import numpy

############################# MODULES ###############################

# Let's start with importing the inputfile classes. 
# Hidden classes have to be imported explicitely.

from input_classes import *
from input_classes import _unsupported_fragment
from input_classes import _fragment


def _readcartesian(filename):
    infile = open(filename,"r")
    content = infile.readlines()
    Natoms = content[0].strip()
    
    re_file = cartesian(title=content[1].strip())
    re_file._cartesian__Natoms = Natoms
    
    for k in range(int(Natoms)):
        dummy = (content[k+2]).split()
        re_file.list_of_atoms.append(dummy)
    re_file.fix()
    return re_file


def _readzmat(filename):
    infile = open(filename,"r")
    re_file = zmat()
    switch = 0
    for k in infile.readlines():
        dummy = k.strip()
        if dummy == "":
            switch += 1
        else:
            if switch == 0:
                re_file.add_atom(dummy)
            if switch == 1:
                re_file.variable((dummy.split())[0],(dummy.split())[1])
            else:
                pass
    return re_file

def _readtinker(filename):
    infile = open(filename,"r")
    content = infile.readlines()
    Natoms = ((content[0]).split())[0]
    titleline = ' '.join(((content[0]).split())[1:])
    
    re_file = tinker(title="")
    re_file._tinker__Natoms = Natoms
    re_file._tinker__title =  titleline
    
    for k in range(int(Natoms)):
        dummy = (content[k+1]).split()
        if len(dummy)<10:
            for k in range(10-len(dummy)):
                dummy.append("0")
            re_file.list_of_atoms.append(dummy[1:])
        else:
            re_file.list_of_atoms.append(dummy[1:])
            
    return re_file


def _readinput(file_input):
    
    #Check input type
    if type(file_input)==list:
        full_content = file_input
    else:
        infile = open(file_input,"r")
        full_content = infile.readlines()
    
    # Get the basic structure 
    
    block_index = [[],[]]
    blocks = []
    switch = 1
    for num, line in enumerate(full_content):
        if "$" in line:
            if switch == 1:
                (block_index[0]).append(num)
                blocks.append((line.strip().lower())[1:])
                switch = 0
            elif switch == 0:
                (block_index[1]).append(num)
                switch = 1
    
    # Create inputfile object
    
    re_file = inputfile() 
    
    # Start to populate the job object with fragments,
    # using the blocks from above and their range,
    # then extend fragments list...
    
    
    for i,k in enumerate(blocks):
        
        # Grab block content and save it to list
        content = full_content[block_index[0][i]+1:block_index[1][i]]

        if k=="rem":
            new_fragment = rem_fragment()
            for k in content:
                new_fragment.add(k.strip().split()[0],k.strip().replace("=","").split()[1])
            re_file.add(new_fragment)
            
        elif k=="molecule":
            if "read" or "READ" in content[0].strip():
                new_fragment = mol_fragment(geometry="read")
            else:
                new_fragment = mol_fragment()
                new_fragment.charge(content[0].strip().split()[0])
                new_fragment.multiplicity(content[0].strip().split()[1])
            
                # What type of coordinates do we have?
                if len(content)<2:
                	switch = 0
                else:
                    switch = len(content[1].strip().split())
                
                if switch == 4:
                    # must be cartesian...
                    cartesian_dummy = cartesian()
                    for line in content[1:]:
                        atom_input = line.strip().split()
                        atom = atom_input[0]
                        x = atom_input[1]
                        y = atom_input[2]
                        z = atom_input[3]
                        cartesian_dummy.add_atom(atom,x,y,z)
                    new_fragment.geometry(cartesian_dummy)
                
                elif switch == 1:
                    # must be zmat...
                    zmat_dummy = zmat()
                    z_switch = 0
                    for line in content[1:]:
                        dummy = line.strip()
                        if dummy == "":
                            z_switch += 1
                        else:
                            if z_switch == 0:
                                zmat_dummy.add_atom(dummy)
                            elif z_switch == 1:
                                zmat_dummy.variable((dummy.split())[0],(dummy.split())[1])
                            else:
                                pass
                    new_fragment.geometry(zmat_dummy)
                
                elif switch > 4:
                    # must be tinker...
                    tinker_dummy = tinker()
                    for line in content[1:]:
                        atom_input = line.strip().split()
                        name = atom_input[0]
                        x = atom_input[1]
                        y = atom_input[2]
                        z = atom_input[3]
                        atomtype = atom_input[4]
                        con1 = atom_input[5]
                        con2 = atom_input[6]
                        con3 = atom_input[7]
                        con4 = atom_input[8]
                        tinker_dummy.add_atom(name,x,y,z,atomtype,con1,con2,con3,con4)
                    new_fragment.geometry(tinker_dummy)
                elif switch == 0:
                	print "Warning: $molecule array is empty."
                else:
                    print "Unknown format in $molecule array."
            re_file.add(new_fragment)
            
        elif k=="comment":
            ret_str = ""
            for line in content:
                ret_str += line
            new_fragment = comment_fragment(ret_str)
            re_file.add(new_fragment)
            
        elif k=="basis":
            new_fragment = basis_fragment()
            first = 0
            atom = content[0].strip()
            for line in content[1:]:
                dummy = line.strip()
                if dummy=="****":
                    first = 1
                else:
                    if first==1:
                        atom = dummy
                        first = 0
                    else:
                        new_fragment.add(atom,dummy)
            re_file.add(new_fragment)


        elif k=="ecp":
            new_fragment = ecp_fragment()
            first = 0
            atom = content[0].strip()
            for line in content[1:]:
                dummy = line.strip()
                if dummy=="****":
                    first = 1
                else:
                    if first==1:
                        atom = dummy
                        first = 0
                    else:
                        new_fragment.add(atom,dummy)
            re_file.add(new_fragment)

        # Add new fragments here...
        #
        # Note: For each added fragment the inputfile class has to be updated
        # so that it recognizes the new fragment type (otherwise it's still unsupported).

        else:
            print "Unsupported array type " + k + " detected. Read as constant."
            new_fragment = _unsupported_fragment(k)
            for line in content:
                new_fragment.add_line(line)
            re_file.add(new_fragment)
            del new_fragment 
            
    # Return the final inputfile object
    return deepcopy(re_file)
    del re_file
    

#Utilities for comparing xyz files taken from https://github.com/charnley/rmsd

#Copyright (c) 2013, Jimmy Charnley Kromann <jimmy@charnley.dk> & Lars Bratholm
#All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:

#1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

def fit(P, Q):
    """ Varies the distance between P and Q, and optimizes rotation for each step
    until a minimum is found.
    """
    step_size = P.max(0)
    threshold = step_size*1e-9
    rmsd_best = kabsch(P, Q)
    while True:
        for i in range(3):
            temp = numpy.zeros(3)
            temp[i] = step_size[i]
            rmsd_new = kabsch(P+temp, Q)
            if rmsd_new < rmsd_best:
                rmsd_best = rmsd_new
                P[:,i] += step_size[i]
            else:
                rmsd_new = kabsch(P-temp, Q)
                if rmsd_new < rmsd_best:
                    rmsd_best = rmsd_new
                    P[:,i] -= step_size[i]
                else:
                    step_size[i] /= 2
        if (step_size<threshold).all():
            break
    return rmsd_best
    
def rmsd(V, W):
    """ Calculate Root-mean-square deviation from two sets of vectors V and W.
    """
    D = len(V[0])
    N = len(V)
    rmsd = 0.0
    for v, w in zip(V, W):
        rmsd += sum([(v[i]-w[i])**2.0 for i in range(D)])
    return numpy.sqrt(rmsd/N)
    
def kabsch(P, Q):
    """ The Kabsch algorithm

    http://en.wikipedia.org/wiki/Kabsch_algorithm

    The algorithm starts with two sets of paired points P and Q.
    P and Q should already be centered on top of each other.

    Each vector set is represented as an NxD matrix, where D is the
    the dimension of the space.

    The algorithm works in three steps:
    - a translation of P and Q
    - the computation of a covariance matrix C
    - computation of the optimal rotation matrix U

    The optimal rotation matrix U is then used to
    rotate P unto Q so the RMSD can be caculated
    from a straight forward fashion.

    """

    # Computation of the covariance matrix
    C = numpy.dot(numpy.transpose(P), Q)

    # Computation of the optimal rotation matrix
    # This can be done using singular value decomposition (SVD)
    # Getting the sign of the det(V)*(W) to decide
    # whether we need to correct our rotation matrix to ensure a
    # right-handed coordinate system.
    # And finally calculating the optimal rotation matrix U
    # see http://en.wikipedia.org/wiki/Kabsch_algorithm
    V, S, W = numpy.linalg.svd(C)
    d = (numpy.linalg.det(V) * numpy.linalg.det(W)) < 0.0

    if(d):
        S[-1] = -S[-1]
        V[:,-1] = -V[:,-1]

    # Create Rotation matrix U
    U = numpy.dot(V, W)

    # Rotate P
    P = numpy.dot(P, U)

    return rmsd(P,Q)