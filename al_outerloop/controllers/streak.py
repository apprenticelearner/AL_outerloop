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


class Streak(OuterLoopController):
    def __init__(self):
        super().__init__()

    def new_student(self, student_id, action_space=None, outer_loop_args = None):
        super().new_student(student_id, action_space)
        
        self.kcs = outer_loop_args['kcs']
        self.interface_to_kc = outer_loop_args['interface_to_kc']

        self.correct_counts = {kc: 0 for kc in self.kcs}
        self.num_problems = 0

        self.choose_max_unmastered = True
        if 'choose_max_unmastered' in outer_loop_args:
            self.choose_max_unmastered = outer_loop_args['choose_max_unmastered']

        # default streak threshold
        self.streak_threshold = 3
        if 'streak_threshold' in outer_loop_args:
            self.streak_threshold = outer_loop_args['streak_threshold']

        # default max problems of 150
        self.max_problems = 150
        if 'max_problems' in outer_loop_args:
            self.max_problems = outer_loop_args['max_problems']

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

        # print("self.problems_by_skill")
        # print(self.problems_by_skill)
        
    def resolve_kcs(self, step):
        kc_list = self.current_prob['kc_list']
        kc_list2 = self.interface_to_kc[step]
        return set(kc_list).intersection(set(kc_list2))

        
    def update(self, step, reward, action_type):
        # 0/1 for correct incorrect rather than a string to print
        correctness_numeric = 1 if reward > 0 and action_type == "ATTEMPT" else 0
        
        if(action_type == "ATTEMPT"):
            correctness = Back.GREEN + "correct" if reward > 0 else Back.RED + "incorrect"
        else:
            correctness = Back.BLUE + "example"

        # Print out information about performance
        print(Fore.CYAN + "Streak Controller Udpate:", step, reward, correctness)
        
        # This controller updates the knowledge component based on the interface marked in the
        # Selection field - here, that corresponds to the step variable.
        kcs = self.resolve_kcs(step)

        for skill in kcs:
            if skill not in self.correct_counts:
                print("ERROR:", skill, "not included in kc_list adding... (",
                        problem_name, ", ", step, ")")
                self.correct_counts[skill] = 0

            if correctness_numeric == 1:
                self.correct_counts[skill] += 1
            else:
                self.correct_counts[skill] = 0

        print("Correctness count for %s after update: %i" % (skill, self.correct_count[skill]))

    def get_problem_kcs(self, problem):
        if("kc_list" in problem):
            kcs = problem["kc_list"]
        else:
            raise ValueError("Problem objects must have attribute 'kc_list'")

        return kcs



    def all_skills_mastered(self):
        '''
        Returns true if all skills that we have problems for are above mastery threshold
        '''
        for skill in self.correct_counts:
            if (skill in self.problems_by_skill and
                    self.correct_counts[skill] <= self.streak_threshold):
                return False
        return True
        
    def next_problem(self,student=None):
        self.num_problems += 1
        
        if self.all_skills_mastered() or len(self.rewards) > max_problems:
            # All skills have been mastered or we've asked as many
            # problems as allowed - stop training.
            self.test_mode  = True;
            print("Mastery estimates when entering testing:", self.correct_counts)
            print("Skills mastered:", self.all_skills_mastered())
        
        if self.test_mode:
            if len(self.test_set) > 0:
                nxt = self.test_set.pop(0)
                nxt["test_mode"] = True
                return nxt
            else:
                print("Problems in training ( total number =", len(self.problems_asked),")")
                print(self.problems_asked)
                return None # done training
        else:
            print("Asking for problem ", self.num_problems)
            print("Mastery_Probabilities: ",self.correct_count)
            # Choose a problem with the most unmastered skills 
            
            max_unmastered_kcs = 0
            problem_with_max_unmastered_kcs = []
            for problem in self.action_space:
                kcs = self.get_problem_kcs(problem)
                # if bkt_config.get("single_kc", False):
                #     skills = problem["kc_list"]
                # else:
                #     skills = ["single_kc"]
                
                # Check how many skills that are used in this problem are unmastered
                unmastered_kcs = [kc for kc in kcs if self.correct_counts[kc] < self.streak_threshold]
                if self.choose_max_unmastered:
                    if len(unmastered_kcs) > max_unmastered_kcs:
                        max_unmastered_kcs = len(unmastered_kcs)
                        problem_with_max_unmastered_kcs = [problem]
                    elif len(unmastered_kcs) == max_unmastered_kcs: # We'll choose randomly among problems with the same number of unmastered skills
                        problem_with_max_unmastered_kcs.append(problem)
                else:
                    problem_with_max_unmastered_kcs.append(problem)
                    
            # print("Number of problems with", max_unmastered_kcs, "unmastered skills:", len(problem_with_max_unmastered_kcs))
            # Choose a random problem from problems with the maximum unmastered skills
            nxt = choice(problem_with_max_unmastered_kcs)
            self.problems_asked.append(nxt["question_file"])
            self.current_prob = nxt
            # print("N",nxt)
            return nxt
       
