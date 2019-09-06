
class OuterLoopController(object):
	def __init__(self):
		self.is_initialized = False

	def new_student(self, student_id, action_space=None, outer_loop_args = None):
		self.current_student = student_id
		self.is_initialized = True
        
        # Separate the action_space into training (action_space)
        num_test_problems = -1
        if "num_test_problems" in outer_loop_args:
            num_test_problems = outer_loop_args["num_test_problems"]
            
        if num_test_problems > 0:
            train = len(action_space) - num_test_problems      
            self.action_space = action_space[:train]
            self.test_set = action_space[train:]       
        else:
            self.action_space = action_space
            self.test_set = []

	def update(self,step,reward,feedback_type,question_file):
		pass

	def next_problem(self,student=None):
		raise NotImplementedError()

