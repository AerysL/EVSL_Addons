# This is a very rough retriever of the test matrices used in the paper.
import tarfile
import gzip
import urllib
import os.path
matrix_type = "MM"
matrix_group = "PARSEC"
matrices = ["Ge87H76", "Ge99H100", "Si41Ge41H72", "Si87H76",
"Ga41As41H72"]
limits = [ ("-0.64", "-0.0053"), ("-0.65", "-0.0096"), ("-0.64",
"-0.0028"), ("-0.66", "-0.0300"), ("-0.64", "-0.0000")]

if __name__ == "__main__":
    for (matrix,limit) in zip(matrices,limits):
        if os.path.isfile('%s.mtx' % matrix):
            continue
        else:
            print("Matrix %s does not exist, will download" % matrix)
            url = 'https://www.cise.ufl.edu/research/sparse/%s/%s/%s.tar.gz' % (matrix_type, matrix_group, matrix)
            f =  urllib.urlopen(url)
            matrix_dl = f.read()
            f.close()
            matrix_file = open('%s.tar.gz' % matrix, 'w')
            matrix_file.write(matrix_dl)
            matrix_file.close()
            print('Opening tar.gz file')
            tar = tarfile.open('%s.tar.gz' % matrix, 'r:gz')
            tar.extractall()
            tar.close()
            os.rename('%s/%s.mtx' % (matrix,matrix), '%s.mtx' %
                    (matrix))
            os.remove('%s.tar.gz' % matrix)
            os.rmdir('%s' % matrix)
            print('Finished extracting %s' % matrix)
            print('Writing matfile for %s' % matrix)
            matfile = open('matfile-%s' % matrix, 'w')
            matfile.write('1\n')
            matfile.write('%s.mtx %s MM1 %s %s 1' % (matrix, matrix,
                limit[0], limit[1]))
            matfile.write("""
            First line  is the number  of matrices to  be tested [called  numat in
            drivers]. 2nd  line contains  the path  to the  matrix, followed  by a
            short name  for the  matrix, the  datatype of  the input  matrix, left
            endpoint  of  the  target  interval,  right  endpoint  of  the  target
            interval, and  the number of  slices in  which to divide  the interval
            This 2nd line is repeated for as many matrices as indicated by numat
            
            Datatype:
            
            MM0 = matrix market with indexing starting at 0 (as in C)
            
            MM1 = matrix market with indexing starting at 1 (as in Fortran)""")
            matfile.close()
            print('Done writing matfile')
