from .base import OuterLoopController
from random import choice

Q_literalField = {'hint':'hint', 'done':'done', 'JCommTable4.R0C0':'num3','JCommTable4.R1C0':'den3', 'JCommTable5.R0C0':'num4', 'JCommTable5.R1C0':'den4', 'JCommTable6.R0C0':'num5', 'JCommTable6.R1C0':'den5', 'JCommTable8.R0C0':'check_convert', 'checkBoxGroup': 'check_convert'}
Q_field = {'num3': 'num5', 'den3': 'den5'}

class Random(OuterLoopController):
	def new_student(self, student_id, action_space=None):
		self.current_student = student_id
		split = int(len(action_space) * .1)
		
		self.action_space = action_space[:split]
		self.test_set = action_space[split:]

		self.is_initialized = True

	def update(self,step,reward,feedback_type,problem_name):
		correctness = "\x1b[0;30;42m correct\x1b[0m" if reward > 0 and feedback_type == "correctness" else "\x1b[0;30;41m incorrect\x1b[0m"
		kc = Q_literalField[step]
		if(kc in Q_field):
			kc = Q_field[kc]
		kc = problem_name.split(" ")[0] + " "+ kc
		print("RL_AGENT UPDATE:",step,kc, reward,correctness,problem_name)
		# rewards.append(reward)
		# steps.append(step)
		# tps.append(feedback_type)
		# print(rewards)
		# print(steps)
		# print(tps)


	def next_problem(self,student=None):
		if(len(self.action_space) > 0):
			nxt = choice(self.action_space)
			self.action_space.remove(nxt)
			return nxt
		elif(len(self.test_set) > 0):
			nxt = self.test_set.pop(0)
			nxt["test_mode"] = True
			return nxt
		else:
			return {}

