import random
import numpy as np
import pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from util import *

class Actor(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(Actor, self).__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, output_size)
        
    def forward(self, s):
        x = F.relu(self.linear1(s))
        x = F.relu(self.linear2(x))
        x = torch.tanh(self.linear3(x))

        return x

class Critic(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, s, a):
        x = torch.cat([s, a], 1)
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = self.linear3(x)

        return x

class Agent(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # assign to self variables

        self.actor = Actor(self.s_dim, 256, self.a_dim).cuda()
        self.actor_target = Actor(self.s_dim, 256, self.a_dim).cuda()
        self.critic = Critic(self.s_dim + self.a_dim, 256, self.a_dim).cuda()
        self.critic_target = Critic(self.s_dim + self.a_dim, 256, self.a_dim).cuda()
        self.actor_optim = optim.Adam(self.actor.parameters(), lr = self.actor_lr)
        self.critic_optim = optim.Adam(self.critic.parameters(), lr = self.critic_lr)
        self.buffer = []
        
        self.actor_target.load_state_dict(self.actor.state_dict())
        self.critic_target.load_state_dict(self.critic.state_dict())

    def load_trained_actor(self):
        self.actor = torch.load(self.model_path) # pt
        
    def act(self, s0):
        s0 = torch.tensor(s0, dtype=torch.float).cuda()
        a0 = self.actor(s0).squeeze(0).detach().cpu() # detach only for collecting samples.
        return a0 
    
    def put(self, *transition): 
        if len(self.buffer)== self.capacity:
            self.buffer.pop(0)  
        self.buffer.append(transition)
    
    def learn(self):
        if len(self.buffer) < self.batch_size:
            return 
        
        samples = random.sample(self.buffer, self.batch_size)
        
        s0, a0, r1, s1 = zip(*samples)

        s0 = torch.tensor(s0, dtype=torch.float).cuda() # [[s], [s], [s]]
        a0 = torch.tensor(a0, dtype=torch.float).view(self.batch_size,-1).cuda() # [[a], [a], [a]]
        r1 = torch.tensor(r1, dtype=torch.float).view(self.batch_size,-1).cuda()
        s1 = torch.tensor(s1, dtype=torch.float).cuda()
        
        def critic_learn():
            # not update target network here
            a1 = self.actor_target(s1).detach()
            y_true = r1 + self.gamma * self.critic_target(s1, a1).detach()
            
            y_pred = self.critic(s0, a0) # actor not updated here, since detached
            
            loss_fn = nn.MSELoss()
            loss = loss_fn(y_pred, y_true)
            self.critic_optim.zero_grad()
            loss.backward()
            self.critic_optim.step()
            
        def actor_learn():
            loss = -torch.mean( self.critic(s0, self.actor(s0)) ) # actor updated here
            self.actor_optim.zero_grad()
            loss.backward()
            self.actor_optim.step()
                                           
        def soft_update(net_target, net, tau):
            for target_param, param in zip(net_target.parameters(), net.parameters()):
                target_param.data.copy_(target_param.data * (1.0 - tau) + param.data * tau)
    
        critic_learn()
        actor_learn()
        soft_update(self.critic_target, self.critic, self.tau)
        soft_update(self.actor_target, self.actor, self.tau)

    def train(self, max_iters):
        with open(self.exp_path, "rb") as fo:
            self.buffer = pickle.load(fo, encoding='bytes')
        for i in range(max_iters):
            self.learn()
            if i % 1000 == 0:
                print("trained for one iter")
        
        torch.save(self.actor, self.model_path)

if __name__ == '__main__':
    ddpg = Agent(**params)
    ddpg.train(max_iters=10000)
