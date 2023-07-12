import torch
from transformers import GPT2Tokenizer, GPT2DoubleHeadsModel, GPT2Config

def get_model_size(model):
    param_size = 0
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()

    print('model parameters size: {:.3f}MB'.format(param_size/1024/1024))

tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
configuration = GPT2Config(n_layer=48)
model = GPT2DoubleHeadsModel(configuration)
print(configuration)
get_model_size(model)