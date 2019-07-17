
class OuterLoopController(object):
	def __init__(self):
		self.is_initialized = False

	def new_student(self, student_id, action_space=None):
		self.current_student = student_id
		self.action_space = action_space
		self.is_initialized = True

	def update(self,step,reward,feedback_type,question_file):
		pass

	def next_problem(self,student=None):
		raise NotImplementedError()

