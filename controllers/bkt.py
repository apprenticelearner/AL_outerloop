from .base import OuterLoopController
from random import choice
import json
import sys,os,inspect

mastery_threshold = .95 #Stop asking about a skill if estimate of mastery is > threshold
max_problems = 50 #Stop asking problems if after max_problems

# This is the path to AL_outerloop/ExampleJSON/bkt_config.json
config_file = os.path.join('ExampleJSON', 'bkt_config.json') # File with the BKT probabilities

class BKT(OuterLoopController):
    def __init__(self):
        '''
        Sets up the controller by reading in the BKT probabilities
        from a json. The BKT probabilities have four probabilities
        for each skill:         
        - known: the probability the skill is already learned before any practice attempts
        - learn: the probability of learning the skill on a single practice attempt
        - guess: the probability a learner will answer correctly despite not knowing a skill
        - slip: the probability a learner will answer incorrectly despite knowing a skill 
        '''
        super().__init__()
        read_config_json(config_file)

    def new_student(self, student_id, action_space=None):
        super().new_student(student_id, action_space)
        # Track the steps for each problem, rewards, and feedback types.
        self.steps = []
        self.rewards = []
        self.tps = []

        split = 10 # default test_set size is 10
        if len(action_space) > split:      
            self.action_space = action_space[:-split]
            self.test_set = action_space[-split:]
        else:
            self.action_space = action_space
            self.test_set = []
        
        # Initialize our estimate of whether the agent knows each skill
        # each estimate is just the probability the skill is known before practice
        self.mastery_prob = {skill: bkt_probs[skill]["known"] for skill in bkt_probs}
        
        # Whether we're in testing or training - we'll only start in test mode if
        # the probability known is higher than the threshold for all skills.
        # (This generally shouldn't happen.)
        self.test_mode = False # We start off in training mode
        
        # Map each problem to a skill (the three skills here are M , AD, and AS:
        # fraction multiplication, fraction addition with different denominators,
        # and fraction addition with the same denominators)
        self.problems_by_skill = {}
        for problem in self.action_space:
            item = problem["question_file"]
            if item[item.rindex("/")+1:][:2] not in self.problems_by_skill:
                self.problems_by_skill[item[item.rindex("/")+1:][:2]] = []
            self.problems_by_skill[item[item.rindex("/")+1:][:2]].append(problem)
        
    
    def update(self,step,reward,feedback_type,problem_name):
        correctness = "\x1b[0;30;42m correct\x1b[0m" if reward > 0 and feedback_type == "correctness" else "\x1b[0;30;41m incorrect\x1b[0m"
        # 0/1 for correct incorrect rather than a string to print
        correctness_numeric = 1 if reward > 0 and feedback_type == "correctness" else 0
        
        print("RL_AGENT UPDATE:",step, reward,correctness,problem_name)
        self.rewards[-1].append(correctness_numeric)
        self.steps[-1].append(step)
        self.tps[-1].append(feedback_type)
        
        if step == "done" and reward == 1:
            # Problem is finished, update skill(s)
            
            # For simple example, skill is just based on the problem 
            skill = problem_name[:2]
            
            if sum(self.rewards[-1]) == len(self.rewards[-1]):
                # All were correct
                p_obs = [bkt_probs[skill]["guess"], 1-bkt_probs[skill]["slip"]]
            else:
                # At least one incorrect, which we'll treat as incorrect
                p_obs = [1-bkt_probs[skill]["guess"], bkt_probs[skill]["slip"]]
        
            # Probability not yet learned is proportional to not learning it now and having not learned previously
            p_not_learned = (1-bkt_probs[skill]["learn"])*p_obs[0]*(1-self.mastery_prob[skill])
            # Probability learned proportional to sum of having just learned it and having already learned it
            p_learned = bkt_probs[skill]["learn"]*p_obs[0]*(1-self.mastery_prob[skill]) + p_obs[1]*self.mastery_prob[skill]
            
            # Normalize to get new mastery prob for this skill
            self.mastery_prob[skill] = p_learned / (p_learned + p_not_learned)

    def all_skills_mastered(self):
        '''
        Returns true if all skills are above mastery threshold
        '''
        return all([self.mastery_prob[skill] > mastery_threshold for skill in self.mastery_prob])
        
    def next_problem(self,student=None):
        # Start tracking of new problem
        # if len(self.rewards) > 0:
        #     print(self.rewards[-1])
        #     print(self.steps[-1])
        #     print(self.tps[-1])
        self.rewards.append([])
        self.steps.append([])
        self.tps.append([])
        
        
        if self.all_skills_mastered() or len(self.rewards) > max_problems:
            # All skills have been mastered or we've asked as many
            # problems as allowed - stop training.
            self.test_mode  = True;
            print("Mastery estimates when entering testing:",self.mastery_prob)
        
        if self.test_mode:
            if len(self.test_set) > 0:
                nxt = self.test_set.pop(0)
                nxt["test_mode"] = True
                return nxt
            else:
                return {} # done training
        else:
            print("Asking for problem ", len(self.rewards))
            print(self.mastery_prob)
            # Choose a random skill among all those that are unmastered
            nxt_skill = choice([skill for skill in self.mastery_prob if self.mastery_prob[skill] < mastery_threshold])
            print("Target skill", nxt_skill)
            # Choose a random problem from problems for the target skill
            problems = self.problems_by_skill[nxt_skill]
            nxt = choice(problems)
            print("N",nxt)
            return nxt
       

def read_config_json(json_file):
    split_path = os.path.abspath(inspect.stack()[0][1]).split("controllers")
    # print(os.getcwd())
    json_path = os.path.join(split_path[0],json_file)
    with open(json_path) as f:
        config = json.load(f)
    global bkt_probs
    bkt_probs = config["bkt_probs"]