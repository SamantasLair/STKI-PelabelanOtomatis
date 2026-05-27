import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

checkpoint_path = './results/checkpoint-800'
original_model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

tokenizer = AutoTokenizer.from_pretrained(original_model_name)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint_path)
model.eval()

# MONKEY PATCH FOR ONNX EXPORT (Transformers 4.46+)
def onnx_friendly_create_attention_masks(self, attention_mask, input_shape, device, past_key_values_length=0, **kwargs):
    extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
    extended_attention_mask = extended_attention_mask.to(dtype=self.dtype)
    extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0
    return extended_attention_mask, None

import types
model.base_model._create_attention_masks = types.MethodType(onnx_friendly_create_attention_masks, model.base_model)

MAX_LENGTH = 128
dummy_input = {
    'input_ids': torch.zeros((1, MAX_LENGTH), dtype=torch.long),
    'attention_mask': torch.zeros((1, MAX_LENGTH), dtype=torch.long)
}

class ONNXExportWrapper(torch.nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model
        
    def forward(self, input_ids, attention_mask):
        outputs = self.base_model(
            input_ids=input_ids, 
            attention_mask=attention_mask,
            return_dict=False
        )
        return outputs[0]

export_model = ONNXExportWrapper(model.base_model).cpu()
onnx_path = 'temp_patched_model.onnx'

try:
    torch.onnx.export(
        export_model,
        (dummy_input['input_ids'], dummy_input['attention_mask']),
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_ids', 'attention_mask'],
        output_names=['last_hidden_state'],
        dynamic_axes={
            'input_ids': {0: 'batch_size', 1: 'sequence_length'},
            'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
            'last_hidden_state': {0: 'batch_size', 1: 'sequence_length'}
        }
    )
    print('SUCCESS! Monkey Patch worked.')
except Exception as e:
    import traceback
    traceback.print_exc()
