from .base import OuterLoopController
from random import choice
import json
import sys,os,inspect
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)


#######
# This version of the BKT controller updates
# mastery probabilities by treating every interface component
# (in the Selection field) as a separate KC, and choosing a 
# problem with the most unmastered KCs. It must be used with
# an action_space that specifies the KCs in the problem set. 
# Chooses a problem with the maximum number of unm
#
# Options specifiable via outerloop_args:
# bkt_probs (required) : Specifies the BKT probabilities for each skill:
#        - known: the probability the skill is already learned before any practice attempts
#        - learn: the probability of learning the skill on a single practice attempt
#        - guess: the probability a learner will answer correctly despite not knowing a skill
#        - slip: the probability a learner will answer incorrectly despite knowing a skill 
# num_test_problems : number of problems to use for testing (not training);
#    these problems will be the final problems specified in the action_space.
# interface_to_skill : a mapping between each interface component and skill 
#     If not included, raw interface components are skills. If this maps everything
#     to an empty string, than include_problem_start_in_kc can be used to map
#     all steps in a problem to the same skill.
# single_kc : all attempts use the same kc
# include_problem_start_in_kc : in addition to the interface component
#     skills will include any part of the problem name that occurs before a space,
#     or if num_chars_problem_start is included as well, that number of characters
#     from the problem name
#######

mastery_threshold = .95 #Stop asking about a skill if estimate of mastery is > threshold
max_problems = 150 #Stop asking problems if after max_problems


class BKT(OuterLoopController):
    def __init__(self):
        super().__init__()

    def new_student(self, student_id, action_space=None, outer_loop_args = None):
        super().new_student(student_id, action_space)
        
        # Load BKT information
        global bkt_probs
        bkt_probs = outer_loop_args["bkt_probs"]
        # global bkt_config
        self.bkt_config = outer_loop_args

        self.choose_max_unmastered = True
        if 'choose_max_unmastered' in outer_loop_args:
            self.choose_max_unmastered = outer_loop_args['choose_max_unmastered']

        self.reuse_problems = False
        if 'reuse_problems' in outer_loop_args:
            self.reuse_problems = outer_loop_args['reuse_problems']
        
        # Track the steps for each problem, rewards, and feedback types.
        self.steps = []
        self.rewards = []
        self.tps = []
        self.problems_asked = []
        
        # Initialize our estimate of whether the agent knows each skill
        # each estimate is just the probability the skill is known before practice
        self.mastery_prob = {skill: bkt_probs[skill]["known"] for skill in bkt_probs}

        # Whether we're in testing or training - we'll only start in test mode if
        # the probability known is higher than the threshold for all skills.
        # (This generally shouldn't happen.)
        self.test_mode = False # We start off in training mode
        
        # Map each problem to a skill
        self.problems_by_skill = {}
        for problem in self.action_space:            
            kcs = self.get_problem_kcs(problem)
            for kc in kcs:
                if kc not in self.problems_by_skill:
                     self.problems_by_skill[kc] = []
                self.problems_by_skill[kc].append(problem)

        self.steps_updated = set()

        # print("self.problems_by_skill")
        # print(self.problems_by_skill)
        
    def map_interface_to_skill(self, problem_name, step):
        ''''
        Returns the skill associated with this step and problem name.
        Behavior depends on two fields in the BKT config file:
        -- If interface_to_skill is present, then the step name is re-mapped to its
            value in interface_to_skill
        -- If include_problem_start_in_kc is true, then the skill begins with any part
             of the problem name that occurs before a space (e.g., if the problem name
             is AD 5_6_plus_1_7.brd, then AD will be prepended before the skill name).
        '''
        skill = step # default is just step name
        if "single_kc" in self.bkt_config:
            # single_kc is set to true in the config file, so
            # we'll make everything the default skill
            skill = "single_kc"  
        else:
            if "interface_to_skill" in self.bkt_config:
                # interface_to_skill appears in our config file, so we'll map
                # the raw Selection names to particular skills
                skill = self.bkt_config["interface_to_skill"][step]
            if self.bkt_config.get("include_problem_start_in_kc",False):
                # include_problem_start_in_kc appears in our config file and maps to true.
                # if there's a num_chars_problem_start in the config then we'll use 
                # that many characters from the problem name. Otherwise,
                # we'll include any prefix to the problem name before a space as part of our skill
                if "num_chars_problem_start" in self.bkt_config:
                    skill = problem_name[:self.bkt_config.get("num_chars_problem_start")] + " " + skill
                else:
                    skill = problem_name.split(" ")[0] + " "+ skill

        return skill

    def resolve_kcs(self,step):
        kc_list = self.current_prob['kc_list']
        kc_list2 = self.bkt_config['interface_to_kc'][step]
        return set(kc_list).intersection(set(kc_list2))

        
    def update(self,step,reward,action_type):

        if step in self.steps_updated:
            print('not first attempt, skipping update.')
            return

        self.steps_updated.add(step)

        # 0/1 for correct incorrect rather than a string to print
        correctness_numeric = 1 if reward > 0 and action_type == "ATTEMPT" else 0
        
        if(action_type == "ATTEMPT"):
            correctness = Back.GREEN + "correct" if reward > 0 else Back.RED + "incorrect"
        else:
            correctness = Back.BLUE + "example"

        # Print out information about performance
        print(Fore.CYAN + "RL_CONTROLLER UPDATE:", step, reward, correctness)
        # print("RL_AGENT UPDATE:",step, reward,correctness,problem_name)
        self.rewards[-1].append(correctness_numeric)
        self.steps[-1].append(step)
        self.tps[-1].append(action_type)
        
        # This controller updates the knowledge component based on the interface marked in the
        # Selection field - here, that corresponds to the step variable.
        kcs = self.current_prob['kc_list'] if 'interface_to_kc' not in self.bkt_config else self.resolve_kcs(step)
        print("KCS being updated", kcs)
        for skill in kcs:
            # skill = self.current_prob['kc_list'][0]#self.map_interface_to_skill(problem_name, step)
            if skill not in bkt_probs:
                print("ERROR:", skill, "not included in BKT probabilities. (", problem_name, ", ", step, ")")
            
            if correctness_numeric == 1:
                # Step was correct
                p_obs = [bkt_probs[skill]["guess"], 1-bkt_probs[skill]["slip"]]
            else:
                # Step was incorrect
                p_obs = [1-bkt_probs[skill]["guess"], bkt_probs[skill]["slip"]]
            
            # Probability not yet learned is proportional to not learning it now and having not learned previously
            p_not_learned = (1-bkt_probs[skill]["learn"])*p_obs[0]*(1-self.mastery_prob[skill])
            # Probability learned proportional to sum of having just learned it and having already learned it
            p_learned = bkt_probs[skill]["learn"]*p_obs[0]*(1-self.mastery_prob[skill]) + p_obs[1]*self.mastery_prob[skill]
                
            # Normalize to get new mastery prob for this skill
            self.mastery_prob[skill] = p_learned / (p_learned + p_not_learned)
        print("Mastery prob after update:",self.mastery_prob)

    def get_problem_kcs(self,problem):
        if "single_kc" in self.bkt_config:
            kcs = ["single_kc"]
        elif("kc_list" in problem):
            kcs = problem["kc_list"]
        else:
            raise ValueError("Problem objects must have attribute 'kc_list'")

        return kcs



    def all_skills_mastered(self):
        '''
        Returns true if all skills that we have problems for are above mastery threshold
        '''
        for skill in self.mastery_prob:
            if skill in self.problems_by_skill and self.mastery_prob[skill] <= mastery_threshold:
                return False
        return True
        
    def next_problem(self,student=None):

        # Reset the steps updated to empty set
        self.steps_updated = set()

        # Start tracking of new problem
        self.rewards.append([])
        self.steps.append([])
        self.tps.append([])

        if (self.all_skills_mastered() or len(self.rewards) > max_problems or
                len(self.action_space) == 0):
            # All skills have been mastered or we've asked as many
            # problems as allowed - stop training.
            self.test_mode  = True;
            print("Mastery estimates when entering testing:",self.mastery_prob)
            print("skills mastered:",self.all_skills_mastered())
        
        if not self.test_mode:
            print("Asking for problem ", len(self.rewards))
            print("Mastery_Probabilities: ",self.mastery_prob)
            # Choose a problem with the most unmastered skills 
            
            max_unmastered_kcs = 0
            problem_with_unmastered_kcs = []
            for problem in self.action_space:
                kcs = self.get_problem_kcs(problem)
                # print('problem kcs', kcs)
                # if bkt_config.get("single_kc", False):
                #     skills = problem["kc_list"]
                # else:
                #     skills = ["single_kc"]
                
                # Check how many skills that are used in this problem are unmastered
                unmastered_kcs = [kc for kc in kcs if self.mastery_prob[kc] <= mastery_threshold]
                if len(unmastered_kcs) == 0:
                    continue
                elif self.choose_max_unmastered:
                    if len(unmastered_kcs) > max_unmastered_kcs:
                        max_unmastered_kcs = len(unmastered_kcs)
                        problem_with_unmastered_kcs = [problem]
                    elif len(unmastered_kcs) == max_unmastered_kcs: # We'll choose randomly among problems with the same number of unmastered skills
                        problem_with_unmastered_kcs.append(problem)
                else:
                    problem_with_unmastered_kcs.append(problem)

            if len(problem_with_unmastered_kcs) == 0:
                self.test_mode  = True;
                log.info("Streak counts when entering testing:", self.correct_counts)
                log.info("Skills mastered:", self.all_skills_mastered())
            else:
                # print("Number of problems with", max_unmastered_kcs, "unmastered skills:", len(problem_with_max_unmastered_kcs))
                # Choose a random problem from problems with the maximum unmastered skills
                nxt = choice(problem_with_unmastered_kcs)

                if not self.reuse_problems:
                    self.action_space.remove(nxt)

                self.problems_asked.append(nxt["question_file"])
                self.current_prob = nxt
                # print("N",nxt)
                return nxt

        if self.test_mode:
            if len(self.test_set) > 0:
                nxt = self.test_set.pop(0)
                nxt["test_mode"] = True
                return nxt
            else:
                print("Problems in training ( total number =", len(self.problems_asked),")")
                print(self.problems_asked)
                return None # done training
