from .base import OuterLoopController
from random import choice


class Random(OuterLoopController):
    def new_student(self, student_id, action_space=None):
        '''
        Initializes the controller to train a new agent.
        '''
        super().new_student(student_id, action_space)
        # Separate the action_space into training (action_space)
        # and test (test_set)
        # We'll use the last 10 to evaluate the agent
        split = 10
        if len(action_space) > split:       
            self.action_space = action_space[:-split]
            self.test_set = action_space[-split:]
        else:
            self.action_space = action_space
            self.test_set = []

    def update(self,step,reward,feedback_type,problem_name):
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
        correctness = "\x1b[0;30;42m correct\x1b[0m" if reward > 0 and feedback_type == "correctness" else "\x1b[0;30;41m incorrect\x1b[0m"
       
        
        # Print out information about performance
        print("RL_CONTROLLER UPDATE:",step, reward,correctness,problem_name)


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
            return {}

