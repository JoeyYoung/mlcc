params = {
        's_dim': 7, #FIXME, modify the state dim
        'a_dim': 1,
        'gamma': 0.99,
        'actor_lr': 0.001,
        'critic_lr': 0.001,
        'tau': 0.02,
        'capacity': 10000,
        'batch_size': 32,
        'model_path': '/home/xyzhao/ccpdemo/baseline/deepcc/actor.pt',
        'exp_path': '/home/xyzhao/ccpdemo/baseline/deepcc/samples.pkl',
}
