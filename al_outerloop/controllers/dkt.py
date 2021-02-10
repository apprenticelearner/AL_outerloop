from .base import OuterLoopController
from random import choice
import json
import sys,os,inspect
import colorama
from colorama import Fore, Back, Style
import logging

from dkt_torch.model_fitting import predict

colorama.init(autoreset=True)
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

kc_mapping = {
    "AD check_convert": "AD JCommTable8.R0C0",
    "AS check_convert": "AS JCommTable8.R0C0",
    "M check_convert": "M  JCommTable8.R0C0",
    "AD done": 'AD done',
    "AS done": 'AS done',
    "M done": 'M  done',
    "AD num3": "AD JCommTable4.R0C0",
    "AS num3": "AS JCommTable4.R0C0",
    "M num3": "M  JCommTable4.R0C0",
    "AD den3": "AD JCommTable4.R1C0",
    "AS den3": "AS JCommTable4.R1C0",
    "M den3": "M  JCommTable4.R1C0",
    "AD num4": "AD JCommTable5.R0C0",
    "AS num4": "AS JCommTable5.R0C0",
    "M num4": "M  JCommTable5.R0C0",
    "AD den4": "AD JCommTable5.R1C0",
    "AS den4": "AS JCommTable5.R1C0",
    "M den4": "M  JCommTable5.R1C0",
    "AD num5": "AD JCommTable6.R0C0",
    "AS num5": "AS JCommTable6.R0C0",
    "M num5": "M  JCommTable6.R0C0",
    "AD den5": "AD JCommTable6.R1C0",
    "AS den5": "AS JCommTable6.R1C0",
    "M den5": "M  JCommTable6.R1C0"
}

class DKT(OuterLoopController):
    def __init__(self):
        super().__init__()

    def new_student(self, student_id, action_space=None, outer_loop_args=None):
        super().new_student(student_id, action_space)

        if 'model_params' not in outer_loop_args:
            raise ValueError("DTK Controller requires `model_params` value that"
                             " provides model parameters.")
        
        # self.kcs = outer_loop_args['kcs']
        self.interface_to_kcs = outer_loop_args['interface_to_kc']
        self.kcs = list(set(kc_mapping[kc] for interface_ele in self.interface_to_kcs for
                            kc in self.interface_to_kcs[interface_ele]))
        self.num_problems = 0

        self.model_params = outer_loop_args['model_params']
        self.kc_seq = []
        self.correct_seq = []
        self.mastery = predict(self.model_params, self.kc_seq, self.correct_seq)[-1]
        self.mastery = {kc: self.mastery[kc] for kc in self.kcs}
        log.info("Initial mastery probs: {}".format(self.mastery))

        self.choose_max_unmastered = False
        if 'choose_max_unmastered' in outer_loop_args:
            self.choose_max_unmastered = outer_loop_args['choose_max_unmastered']

        self.reuse_problems = False
        if 'reuse_problems' in outer_loop_args:
            self.reuse_problems = outer_loop_args['reuse_problems']

        # default mastery threshold
        self.mastery_threshold = 0.95
        if 'mastery_threshold' in outer_loop_args:
            self.mastery_threshold = outer_loop_args['mastery_threshold']

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
        kcs = set(kc_list).intersection(set(kc_list2))
        return [kc_mapping[kc] for kc in kcs]

        
    def update(self, step, reward, action_type):
        if step in self.steps_updated:
            log.info('not first attempt, skipping update.')
            return

        self.steps_updated.add(step)

        # 0/1 for correct incorrect rather than a string to print
        correctness_numeric = 1 if reward > 0 and action_type == "ATTEMPT" else 0
        
        if(action_type == "ATTEMPT"):
            correctness = Back.GREEN + "correct" if reward > 0 else Back.RED + "incorrect"
        else:
            correctness = Back.BLUE + "example"

        # Print out information about performance
        log.info(Fore.CYAN + "DKT Controller Udpate: {} {} {}".format(step, reward, correctness))
        
        # This controller updates the knowledge component based on the interface marked in the
        # Selection field - here, that corresponds to the step variable.
        kcs = self.resolve_kcs(step)

        if len(kcs) == 0:
            log.info("No KC label for step.")

        for skill in kcs:
            if skill not in self.mastery:
                print("ERROR:", skill, "not included in kc_list")

        # do check to ensure KC is in list
        kcs_dict = {kc: 1 for kc in kcs}

        self.kc_seq.append(kcs_dict)
        self.correct_seq.append(correctness_numeric)
        self.mastery = predict(self.model_params, self.kc_seq, self.correct_seq)[-1]
        self.mastery = {kc: self.mastery[kc] for kc in self.kcs}

        log.info("Updated mastery probs: {}".format(self.mastery))

    def get_problem_kcs(self, problem):
        if("kc_list" in problem):
            kcs = problem["kc_list"]
        else:
            raise ValueError("Problem objects must have attribute 'kc_list'")

        return [kc_mapping[kc] for kc in kcs]

    def all_skills_mastered(self):
        '''
        Returns true if all skills that we have problems for are above mastery threshold
        '''
        for skill in self.mastery:
            if (skill in self.problems_by_skill and
                    self.mastery[skill] < self.mastery_threshold):
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
            log.info("Skills mastered: {}".format(self.mastery))
        
        if not self.test_mode:
            log.info("Asking for problem {}".format(self.num_problems))
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
                unmastered_kcs = [kc for kc in kcs if self.mastery[kc] < self.mastery_threshold]
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
                log.info("Skills mastered: {}".format(self.mastery))
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
                log.info("Problems in training ( total number = {} )".format(self.num_problems))
                return None # done training
