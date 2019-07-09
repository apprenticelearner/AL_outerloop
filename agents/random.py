from .base import OuterLoopAgent
from random import choice

class Random(OuterLoopAgent):
	def update(self,step,reward):
		print("RL_AGENT UPDATE:",step, reward)

	def next_problem(self,student=None):
		if(len(self.action_space) > 0):
			nxt = choice(self.action_space)
			self.action_space.remove(nxt)
			print("N",nxt)
			return nxt
		else:
			return {}

