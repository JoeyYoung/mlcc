from transformers import GPT2Model, GPT2LMHeadModel, GPT2Config, GPT2Tokenizer, AdamW
from torchvision import models
import torch.optim as optim
import torch

def getModelParsSize(model):
    param_size = 0
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()

    print('model parameters size: {:.3f}MB'.format(param_size/1024/1024))

# first check how to use STC, then increase model, then nccl+hvd

# model
configuration = GPT2Config()
model = GPT2LMHeadModel(configuration) # default size 474MB
getModelParsSize(model)
model.to('cuda:0')

# optimizer
optimizer = optim.AdamW([{'params': model.parameters()}])

# tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
generated = tokenizer.encode("The Manhattan bridge")
context = torch.tensor([generated]).to('cuda:0')

# iters 
past_key_values = None
for i in range(30):
    output = model(context, past_key_values=past_key_values)
    past_key_values = output.past_key_values
    # 此时获取GPT2模型计算的输出结果hidden_states张量中第二维度最后一个元素的argmax值, 得出的argmax值即为此次GPT2模型迭代
    # 计算生成的下一个token. 注意, 此时若是第一次迭代, 输出结果hidden_states张量的形状为(batch_size, sel_len, n_state);
    # 此时若是第二次及之后的迭代, 输出结果hidden_states张量的形状为(batch_size, 1, n_state), all_head_size=n_state=nx=768.
    token = torch.argmax(output.logits[..., -1, :])

    # 将本次迭代生成的token的张量变为二维张量, 以作为下一次GPT2模型迭代计算的上下文context.
    context = token.unsqueeze(0)
    # 将本次迭代计算生成的token的序列索引变为列表存入generated
    generated += [token.tolist()]

sequence = tokenizer.decode(generated)
sequence = sequence.split(".")[:-1]
print(sequence)


