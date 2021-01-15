from .base import OuterLoopController
from random import choice
import json
import sys,os,inspect
import colorama
from colorama import Fore, Back, Style
import logging

colorama.init(autoreset=True)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Streak(OuterLoopController):
    def __init__(self):
        super().__init__()

    def new_student(self, student_id, action_space=None, outer_loop_args = None):
        super().new_student(student_id, action_space)
        
        # self.kcs = outer_loop_args['kcs']
        self.interface_to_kcs = outer_loop_args['interface_to_kc']
        self.kcs = list(set(kc for interface_ele in self.interface_to_kcs for
                            kc in self.interface_to_kcs[interface_ele]))

        self.correct_counts = {kc: 0 for kc in self.kcs}
        self.num_problems = 0

        self.choose_max_unmastered = False
        if 'choose_max_unmastered' in outer_loop_args:
            self.choose_max_unmastered = outer_loop_args['choose_max_unmastered']

        self.reuse_problems = False
        if 'reuse_problems' in outer_loop_args:
            self.reuse_problems = outer_loop_args['reuse_problems']

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

        self.steps_updated = set()
        
    def resolve_kcs(self, step):
        kc_list = self.current_prob['kc_list']
        kc_list2 = self.interface_to_kcs[step]
        return set(kc_list).intersection(set(kc_list2))

        
    def update(self, step, reward, action_type):
        if step in self.steps_updated:
            print('not first attempt, skipping update.')
            return

        # 0/1 for correct incorrect rather than a string to print
        correctness_numeric = 1 if reward > 0 and action_type == "ATTEMPT" else 0
        
        if(action_type == "ATTEMPT"):
            correctness = Back.GREEN + "correct" if reward > 0 else Back.RED + "incorrect"
        else:
            correctness = Back.BLUE + "example"

        # Print out information about performance
        log.info(Fore.CYAN + "Streak Controller Udpate:", step, reward, correctness)
        
        # This controller updates the knowledge component based on the interface marked in the
        # Selection field - here, that corresponds to the step variable.
        kcs = self.resolve_kcs(step)

        if len(kcs) == 0:
            log.info("No KC label for step.")

        for skill in kcs:
            if skill not in self.correct_counts:
                log.info("ERROR:", skill, "not included in kc_list adding... (",
                        problem_name, ", ", step, ")")
                self.correct_counts[skill] = 0

            if correctness_numeric == 1:
                self.correct_counts[skill] += 1
            else:
                self.correct_counts[skill] = 0

            log.info("Streak count for %s after update: %i" % (skill, self.correct_counts[skill]))

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
                    self.correct_counts[skill] < self.streak_threshold):
                return False
        return True
        
    def next_problem(self,student=None):

        # Reset the steps updated to empty set
        self.steps_updated = set()

        self.num_problems += 1
        
        if (self.all_skills_mastered() or self.num_problems > self.max_problems or
                len(self.action_space) == 0):
            # All skills have been mastered or we've asked as many
            # problems as allowed - stop training.
            self.test_mode  = True;
            log.info("Streak counts when entering testing:", self.correct_counts)
            log.info("Skills mastered:", self.all_skills_mastered())
        
        if not self.test_mode:
            log.info("Asking for problem ", self.num_problems)
            log.info("Streak counts: ", self.correct_counts)
            # Choose a problem with the most unmastered skills 
            
            max_unmastered_kcs = 0
            problem_with_unmastered_kcs = []
            for problem in self.action_space:
                kcs = self.get_problem_kcs(problem)
                # if bkt_config.get("single_kc", False):
                #     skills = problem["kc_list"]
                # else:
                #     skills = ["single_kc"]
                
                # Check how many skills that are used in this problem are unmastered
                unmastered_kcs = [kc for kc in kcs if self.correct_counts[kc] < self.streak_threshold]
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
                # Choose a random problem from problems with the maximum unmastered skills
                nxt = choice(problem_with_unmastered_kcs)

                if not self.reuse_problems:
                    self.action_space.remove(nxt)

                self.current_prob = nxt
                return nxt
       
        if self.test_mode:
            if len(self.test_set) > 0:
                nxt = self.test_set.pop(0)
                nxt["test_mode"] = True
                return nxt
            else:
                log.info("Problems in training ( total number =", self.num_problems,")")
                return None # done training
