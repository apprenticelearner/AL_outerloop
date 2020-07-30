import random

class OuterLoopController(object):
    def __init__(self):
        self.is_initialized = False

    def new_student(self, student_id, action_space=None, outer_loop_args = None):

        self.current_student = student_id
        self.is_initialized = True

        # Separate the action_space into training (action_space)
        num_train_problems = -1
        if outer_loop_args is not None and "num_train_problems" in outer_loop_args:
            num_train_problems = outer_loop_args["num_train_problems"]

        if outer_loop_args is not None and 'test_problems' in outer_loop_args:
            self.test_set = outer_loop_args['test_problems']
        else:
            self.test_set = []

        if num_train_problems == -1:
            num_train_problems = len(action_space)

        self.action_space = []

        ordered_problems = [(i, v) for i, v in enumerate(action_space)]
        random.shuffle(ordered_problems)

        if num_train_problems > 0:
            self.action_space = [v for i,v in sorted(ordered_problems[:num_train_problems])]

    def update(self,step,reward,feedback_type,question_file):
        pass

    def next_problem(self,student=None):
        raise NotImplementedError()

