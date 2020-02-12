from pulp import *
import time



class tools:
    def __init__(self):
        pass


    #converts given set of skills to its coresponding vector according to the universal-skill-set 
    def skills2vec(skill_set,universal_skill_set):

        vec=[0]*len(universal_skill_set)

        for skill in skill_set:
            vec[universal_skill_set.index(skill)]=1
        
        return vec

    #checks if any skill is missing.it returns -1 for the skill missing, otherwise returns 1
    def checkSkills(FB_Skills_vec,Device_Skills_vec):
        #print(FB_Skills_vec,Device_Skills_vec)
        ret=1
        if(len(FB_Skills_vec)==len(Device_Skills_vec)):
            for i in range(len(FB_Skills_vec)):
                
                if (Device_Skills_vec[i]-FB_Skills_vec[i])<0:
                    #print(Device_Skills_vec[i],"-",FB_Skills_vec[i],"=",Device_Skills_vec[i]-FB_Skills_vec[i])
                    return -1
        else:
            print("In tools:checkSkills, Lengths of the skill vector of the device and Function Block must be the same.")

        return ret
        


    def logic2bi(logic):
        if(logic):
            return 1
        else:
            return 0

   


    def biNOT(input):
        if(input==0):
            return 1
        else:
            return 0



    def used(device,deploy):
        global funDevice, returnOne
        if device != funDevice:
            funDevice = device
            returnOne = 0
        if returnOne:
            return 0
        sum = 0
        for fbn in function_blocks:
            sum += deploy[device][fbn]

        if sum == 1:
            returnOne = 1
            return 1
        return 0




class ilp:
    
    def __init__(self, system,preSetupTime=0):
        self.prob=""
        self.preSetupTime=preSetupTime
        self.setupTime = time.time()
        self.system_model=system
        self.universal_hw_skill_set=self.system_model.hw_skills
        self.devices = list(range(len(self.system_model.devices)))
        self.function_blocks = list(range(len(self.system_model.function_blocks)))
        self.num_function_blocks = len(self.system_model.function_blocks)
        self.device_cost = list(range(len(self.system_model.devices)))
        self.device_energy = list(range(len(self.system_model.devices)))
        self.hw_skills=list(range(len(self.universal_hw_skill_set)))
        self.num_segments=len(self.system_model.segments)
        self.num_devices=len(self.system_model.devices)
        self.objTime=time.time()

        self.max_num_function_blocks = 0
        for fbn in self.function_blocks:
            self.max_num_function_blocks += self.system_model.function_blocks[fbn].num_of_copies

        

        self.device_segment = []
        self.device_connected = []
        self.fbn_connected = []

        for fbn in self.function_blocks:
            self.fbn_connected.append([0 for x in self.function_blocks])


        for device in self.devices:
            self.device_segment.append([0 for x in range(self.num_segments)])
            self.device_connected.append([0 for x in self.devices])



        for link in self.system_model.links:
            si=self.system_model.segments.index(link.segment)
            di=self.system_model.devices.index(link.device)
            #print("di:",di,"si:",si)
            self.device_segment[di][si]=1

        for i in self.devices:
            for j in self.devices:
                if i==j:
                    self.device_connected[i][j]=1
                else:
                    for k in range(self.num_segments):
                        if self.device_segment[i][k] == 1 and self.device_segment[j][k] == 1:
                            self.device_connected[i][j] = 1


        self.function_block_skills_vec=[]
        for i,FB in enumerate(self.system_model.function_blocks):
            self.function_block_skills_vec.append(tools.skills2vec(self.system_model.function_blocks[i].hardware,self.universal_hw_skill_set))
        

        self.device_skills_vec=[]
        for i,D in enumerate(self.system_model.devices):
            self.device_skills_vec.append(tools.skills2vec(self.system_model.devices[i].skills,self.universal_hw_skill_set))




        i = 0
        for device_sys in self.system_model.devices:
            self.device_cost[i] = device_sys.cost
            i+=1


        #********** DECISION VARIABLE **********

        self.deploy = LpVariable.dicts("Deploy", (self.devices, self.function_blocks), 0, 1, LpInteger)
        self.usedDevice = LpVariable.dicts('UsedDeviceCeil', (self.devices), 0, 1, LpInteger)
        self.lin = LpVariable.dicts('linear', (self.devices, self.devices, self.function_blocks,self.function_blocks), 0, 1, LpInteger)
        self.setupTime=time.time()- self.setupTime
        
       
    def setObj(self,obj):
        self.obj=obj
    
        #********** OBJECTIVE FUNCTIONS **********
        # OBJECTIVE: Cost
        if obj=='Cost':
            #Minimize cost
            self.prob+=sum((self.usedDevice[i])*self.device_cost[i] for i in self.devices)

        # OBJECTIVE: Energy
        elif obj=='Energy':
            self.prob+=sum((self.usedDevice[i])*self.system_model.devices[i].energy for i in self.devices)
            

        # OBJECTIVE: Number of used devices
        elif obj=='Number of devices':
            self.prob+=sum((self.usedDevice[i]) for i in self.devices)
            

        
        
        
        # OBJECTIVE: SIL
        elif obj=='SIL':
            SIL = sum(self.usedDevice[device]*self.system_model.devices[device].SIL for device in self.devices)
            self.prob+=SIL

        # OBJECTIVE: Minimized coupling
        elif obj=='Functional coupling':
            self.linc = LpVariable.dicts('linearCouplingFObject', ( self.devices, self.function_blocks,self.function_blocks), 0, 1, LpInteger)
            self.prob+= sum(self.fbn_connected[i][j] * self.linc[k][i][j] for i in self.function_blocks  for j in self.function_blocks for k in self.devices )    
        
        elif obj=="Memory usage":
            max_memory_used=0
            MU=""
            for fb in self.system_model.function_blocks:
                max_memory_used+=fb.memory* fb.num_of_copies
            self.device_used_memory = LpVariable.dicts('DeviceUsedMemory', ( self.devices, 'Continuous'))
            for device in self.devices:
                self.device_used_memory[device] = sum(self.deploy[device][fb]*self.system_model.function_blocks[fb].memory for fb in self.function_blocks)/self.system_model.devices[device].memory
                    
            for i in self.devices:
                for j in self.devices:
                     MU+= self.device_used_memory[i]-self.device_used_memory[j]+max_memory_used
            
            self.prob+= MU

        else:
            print("\n\nThe objective funtion for :"+obj+" has not been implemented .\n\n")
            return False
            # OBJECTIVE: Minimized memory usage per device (-> every device shall have the same memory usage)
            # OBJECTIVE: Minimized coupling

        self.objTime=time.time()-self.objTime
        return True


    def run(self,obj):
        self.runTime=time.time()
        #********** LpProblem **********


        self.prob = LpProblem("Deployment-MCODA-"+obj.replace(" ","_"),LpMinimize)


        self.setObj(obj)
        #********** CONSTRAINTS **********

        #BIG M Method
        self.M=100

        for device in self.devices:
            self.prob+= sum(self.deploy[device][fbn] for fbn in self.function_blocks) <= self.usedDevice[device] * self.M


           
        if 'Energy' in self.system_model.constraints:
            #Energy constraint
            self.prob+= sum(self.usedDevice[device]* self.system_model.devices[device].energy for device in self.devices) <= self.system_model.max_energy

            

        if 'HW Stress' in self.system_model.constraints:
            
            #Max number of fb on devices/HW stress
            for device in self.devices:
                self.prob+= sum(self.deploy[device][fbn] for fbn in self.function_blocks) <= self.system_model.devices[device].max_num_of_function_blocks 
       
        if 'Cost' in self.system_model.constraints:
            #Max cost
            self.prob+= sum(self.usedDevice[device]* self.device_cost[device] for device in self.devices) <= self.system_model.max_cost

        if 'Number of devices' in self.system_model.constraints:
            #number of devices
            self.prob+= sum(self.usedDevice[device] for device in self.devices) <= self.system_model.max_num_devices
        

        if 'Memory' in self.system_model.constraints:
            #occupied_memory    
            for device in self.devices:
                self.prob+=  sum((self.deploy[device][fbn] * self.system_model.function_blocks[fbn].memory) for fbn in self.function_blocks ) <= self.system_model.devices[device].memory
        
        if 'HW Skills' in self.system_model.constraints:
        #hardware skills for FB
            for device in self.devices:
                for fbn in self.function_blocks:
                    cond = tools.checkSkills(self.function_block_skills_vec[fbn], self.device_skills_vec[device])
                    self.prob += self.deploy[device][fbn]*cond >= 0 

        if 'RTE Skills' in self.system_model.constraints:
        #RTE skills
            for device in self.devices:
                for fbn in self.function_blocks:
                    cond = tools.checkSkills(self.function_block_skills_vec[fbn], self.device_skills_vec[device])
                    self.prob += self.deploy[device][fbn]*cond >= 0 

        

        if 'SIL' in self.system_model.constraints:
            #SIL
            for device in self.devices:
                for fbn in self.function_blocks:
                    self.prob += self.system_model.function_blocks[fbn].SIL * self.deploy[device][fbn] <= self.system_model.devices[device].SIL,"SIL" + str(device) + str(fbn)


        #Required number of copies / redundency 
        for fbn in self.function_blocks:
            self.prob += sum(self.deploy[device][fbn] for device in self.devices) == self.system_model.function_blocks[fbn].num_of_copies , "Redundency" + str(fbn)

        if 'Security' in self.system_model.constraints:
        # Security
            for fbn in self.function_blocks:
                for device in self.devices:
                    self.prob += self.deploy[device][fbn]*(tools.logic2bi(self.system_model.function_blocks[fbn].sensitive)) <= (tools.biNOT(tools.logic2bi(self.system_model.devices[device].open)))


        
        if 'Functional coupling' in self.system_model.constraints:
            #Constraint for functional coupling
            #  lin[k][l][i][j] == deploy[k][i]*deploy[l][j]
            self.prob+= sum(self.fbn_connected[i][j] * self.lin[k][l][i][j] * self.device_connected[k][l] for i in self.function_blocks  for j in self.function_blocks for k in self.devices  for l in self.devices)  <= self.max_num_function_blocks


            #Constraint for linearisation
            for k in self.devices:  
                for l in self.devices:
                    for i in self.function_blocks:
                        for j in self.function_blocks:
                            self.prob += self.lin[k][l][i][j] <= self.deploy[k][i]

            #Constraint for linearisation
            for k in self.devices:  
                for l in self.devices:
                    for i in self.function_blocks:
                        for j in self.function_blocks:
                            self.prob += self.lin[k][l][i][j] <= self.deploy[l][j]

            #Constraint for linearisation
            for k in self.devices:  
                for l in self.devices:
                    for i in self.function_blocks:
                        for j in self.function_blocks:
                            self.prob +=  self.deploy[l][j]+self.deploy[k][i]<= self.lin[k][l][i][j] + 1





        if self.obj=='Functional coupling':
            #Constraint for functional coupling objective linearlization 
            #  lin[k][i][j] == deploy[k][i]*deploy[k][j]
            
            #Constraint for linearisation
            for k in self.devices:  
                for i in self.function_blocks:
                    for j in self.function_blocks:
                        self.prob += self.linc[k][i][j] <= self.deploy[k][i]

            #Constraint for linearisation
            for k in self.devices:  
                for i in self.function_blocks:
                    for j in self.function_blocks:
                        self.prob += self.linc[k][i][j] <= self.deploy[k][j]

            #Constraint for linearisation
            for k in self.devices:  
                for i in self.function_blocks:
                    for j in self.function_blocks:
                        self.prob +=  self.deploy[k][j]+self.deploy[k][i]<= self.linc[k][i][j] + 1

        # The problem is solved using PuLP's choice of Solver
        self.prob.writeLP("./Modules/Models/"+self.obj+".lp")
        self.prob.solve()

        print("Status for Objective("+self.obj+") is: ", LpStatus[self.prob.status])

        for device in self.system_model.devices:
            device.function_blocks = list()
        for fb in self.system_model.function_blocks:
            fb.devices = list()

        for i in self.devices:
            for j in self.function_blocks:
                if self.deploy[i][j].value() == 1:
                    self.system_model.devices[i].function_blocks.append(self.system_model.function_blocks[j])
                    self.system_model.function_blocks[j].devices.append(self.system_model.devices[i])
        
        prob = None
        if LpStatus[self.prob.status] != 'Optimal':
            return False
        return True

