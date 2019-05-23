import sys, getopt, random, json, time
import numpy as np
import os
from pipeline1.pipeline import tess_pipeline
from astropy.io import fits

def main(argv):
        tpffile = ''
        outputpath = ''
        
        start_time = time.time()

        # parse arguments
        try:
                opts, args = getopt.getopt(argv, "hi:o:",["tpffile=","outputpath="])
        except getopt.GetoptError:
                print('pipeline1.py -i <tpffile> [-o <outputpath>]')
                sys.exit(2)
        for opt, arg in opts:
                if opt == '-h':
                        print('pipeline1.py -i <tpffile> [-o <outputpath>]')
                        sys.exit()
                elif opt in ("-i", "--tpffile"):
                        tpffile = arg
                elif opt in ("-o", "--outputpath"):
                        outputpath = arg
        if tpffile == '':
                print('pipeline1.py -i <tpffile> [-o <outputpath>]')
                sys.exit(2)

        print("Generating light curve file:")
        print("Input file: {}".format(tpffile))
        print('Output path: {}'.format(outputpath))

		# Print file headers
        hdu = fits.open(tpffile)
        X = hdu[0].header['SECTOR']
        TICID = hdu[0].header['TICID']
        Camera = hdu[0].header['CAMERA']
        CCD = hdu[0].header['CCD']
        RA = hdu[0].header['RA_OBJ']
        DEC = hdu[0].header['DEC_OBJ']
        MAG = hdu[0].header['TESSMAG']
        hdu.close()
        print('TICID = {}'.format(str(TICID)))
        print('Sector = {}'.format(str(X)))
        print('Camera = {}'.format(str(Camera)))
        print('CCD = {}'.format(str(CCD)))
        print('RA = {}'.format(str(RA)))
        print('DEC = {}'.format(str(DEC)))
        print('Magnitude = {}'.format(str(MAG)))

        # Execute pipeline 1 (generate lightcurve file)
        data = tess_pipeline(tpffile, '',  outputpath, bads = True, sector = str(X), ticid = str(TICID))
        lightcurvefilename = os.path.join(outputpath, '{}_data.npz'.format(str(tpffile)))
        np.savez_compressed(lightcurvefilename, **data)

        print("Light curve file: {}".format(lightcurvefilename))
        print("Total time: {} sec".format(time.strftime("%H:%M:%S", time.gmtime(time.time()-start_time))))

if __name__ == "__main__":
   main(sys.argv[1:])        
