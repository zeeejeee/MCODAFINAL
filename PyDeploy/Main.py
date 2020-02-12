import argparse
import time
import csv
import os
from Modules.ILPDeploy import ilp

from Modules import PyDeploy





if __name__ == '__main__':
    objs=["Functional coupling","Memory usage","Cost","Energy","Number of devices","SIL"]
    # ********** COMMAND-LINE ARGUMENTS **********
    parser = argparse.ArgumentParser(description='Deploy a 4diac-system')
    parser.add_argument('-m', '--model', help='Path to model file (.sys file)')
    parser.add_argument('-a', '--algorithm', help='Algorithm to use to find the solution')

    args = parser.parse_args()


    # ********** READ MODEL DATA **********
    system_model = PyDeploy.System()

    system_model.parse_xml(args.model)
    

    

    print("Number of function blocks:", len(system_model.function_blocks))
    print("Number of connections between function blocks:", len(system_model.connections))
    print("Number of devices:", len(system_model.devices))


    # ********** RUN SOLVER **********
 

    try:
        if args.algorithm is None:
            args.algorithm = 'ilp'

      
        # *** ILP ***
        if args.algorithm.lower() == 'ilp':
            start_time = time.time()
            print("#######################Running ILP using PULP#############################")
            ilp_system=ilp(system_model)
            for objective in objs:
                start_time = time.time()
                print("-------Running Objecive FUnction:"+objective+"---------")
                #if(ilp_system.setObj(objective)):
                status = ilp_system.run(objective)
                if status == False:
                    print("--- Not successful ---")
                else:
                    end_time = time.time()
                    time_required = end_time - start_time

                    
                    for device in system_model.devices:
                        device.print_mapping()
                    

                    print("Finished deployment synthesis in %.3f seconds." % (time_required))

                            
                            
                    
                    
    except KeyboardInterrupt:
        print("- Stopped deployment synthesis through keyboard interrupt -")
        
    finally:
        
        print('MCODA DONE!')
