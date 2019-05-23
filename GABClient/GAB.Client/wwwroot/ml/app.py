import sys, getopt, random, json, time

def main(argv):
        tpffile = ''
        outputpath = '.'
        
        start_time = time.time()

        # parse arguments
        try:
                opts, args = getopt.getopt(argv, "hi:o:",["tpffile=","outputpath="])
        except getopt.GetoptError:
                print('app.py -i <tpffile> [-o <outputpath>]')
                sys.exit(2)
        for opt, arg in opts:
                if opt == '-h':
                        print('app.py -i <tpffile> [-o <outputpath>]')
                        sys.exit()
                elif opt in ("-i", "--tpffile"):
                        tpffile = arg
                elif opt in ("-o", "--outputpath"):
                        outputpath = arg
        if tpffile == '':
                print('app.py -i <tpffile> [-o <outputpath>]')
                sys.exit(2)

        print('Input file is "', tpffile, '"')
        print('Output path is "', outputpath, '"')

		# Simulate pipeline execution (15 seconds)
        time.sleep(15)

        # Execute pipeline 1 (generate lightcurve file)
        # TODO...
        lightcurvefilename = tpffile + "_lc.fits"
        lcf = open(lightcurvefilename, "w")
        lcf.write("This should be the lightcurve file content in fits format")
        lcf.close()
		
        # Execute pipeline 2 (machine learning prediction)
        # TODO...
        isplanet = bool(random.getrandbits(1))
        probability = random.uniform(0, 1)
        resultfilename = lightcurvefilename.replace(".fits", ".result")
        data = {"lc": lightcurvefilename, "isplanet": isplanet, "probability": round(probability, 3)}
        json_data = json.dumps(data)
        rf = open(resultfilename, "w")
        rf.write(json_data)
        rf.close()		

        print("Light curve file:", lightcurvefilename)
        print("result file:", resultfilename)
        print("Is planet:", isplanet)
        print("Probability: {:.3}".format(probability))
        print("Total time: {:.2} sec".format(time.time()-start_time))

if __name__ == "__main__":
   main(sys.argv[1:])        
