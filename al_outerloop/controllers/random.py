from .base import OuterLoopController
from random import choice
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)


class Random(OuterLoopController):
    def new_student(self, student_id, action_space=None, outer_loop_args = None):
        '''
        Initializes the controller to train a new agent.
        '''
        super().new_student(student_id, action_space, outer_loop_args)

        self.reuse_problems = False
        if 'reuse_problems' in outer_loop_args:
            self.reuse_problems = outer_loop_args['reuse_problems']


    def update(self,step,reward,action_type):
        '''
        Called after every step in the problem to track performance,
        which many policies use for deciding what problem to assign.
        For the random controller, this just prints out and saves 
        the step type and correctness for debugging purposes.
        '''
        # Identify whether the agent is correct (positive reward when
        # evaluating the agent's correctness) or incorrect (negative
        # reward, or positive reward when the agent is asking for a 
        # hint).
        if(action_type == "ATTEMPT"):
            correctness = Back.GREEN + "correct" if reward > 0 else Back.RED + "incorrect"
        else:
            correctness = Back.BLUE + "example"
       
        
        # Print out information about performance
        print(Fore.CYAN + "RL_CONTROLLER UPDATE:",step, reward,correctness)


    def next_problem(self,student=None):
        '''
        Called when the apprentice learner agent needs a new
        problem. Returns a dictionary that should
        either be empty (signals the policy is done tutoring),
        or have at least the key "question_file" indicating
        which question the agent should do.
        '''
        if(len(self.action_space) > 0):
            # The random controller assigns every problem in the
            # action space once, in random order.
            nxt = choice(self.action_space)
            if not reuse_problems:
                self.action_space.remove(nxt)
            return nxt
        elif(len(self.test_set) > 0):
            # Once there are no more problems in the action space,
            # we have the agent solve the problems in the test_set.
            nxt = self.test_set.pop(0)
            # The line below tells the program that the agent shouldn't
            # learn from its encounters in the current problem. If the
            # agent asks for a hint, the step will be marked incorrect, 
            # but the result will be filled in to allow the agent to
            # continue.
            nxt["test_mode"] = True
            return nxt
        else:
            # Signal that the policy is done tutoring.
            return None

