import os
import torch
import types
from transformers import AutoTokenizer, AutoModel

model_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
output_dir = "STKI/onnx_model"
os.makedirs(output_dir, exist_ok=True)

print("Downloading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id)

MAX_LENGTH = 256
dummy_input = {
    "input_ids": torch.zeros((1, MAX_LENGTH), dtype=torch.long),
    "attention_mask": torch.zeros((1, MAX_LENGTH), dtype=torch.long)
}

# Fix SDPA Tracer Bug
def onnx_friendly_create_attention_masks(*args, **kwargs):
    self = args[0]
    attention_mask = args[1] if len(args) > 1 else kwargs.get('attention_mask')
    extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
    extended_attention_mask = extended_attention_mask.to(dtype=self.dtype)
    extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0
    return extended_attention_mask, None

model._create_attention_masks = types.MethodType(onnx_friendly_create_attention_masks, model)

class ONNXWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
    def forward(self, input_ids, attention_mask):
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=False)
        return outputs[0]

wrapped = ONNXWrapper(model)
wrapped.eval()

onnx_path = os.path.join(output_dir, "multi_label_model.onnx")
print("Exporting ONNX...")
torch.onnx.export(
    wrapped,
    (dummy_input["input_ids"], dummy_input["attention_mask"]),
    onnx_path,
    export_params=True,
    opset_version=14,
    do_constant_folding=True,
    input_names=["input_ids", "attention_mask"],
    output_names=["last_hidden_state"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "last_hidden_state": {0: "batch_size", 1: "sequence_length"}
    }
)
tokenizer.save_pretrained(output_dir)
print(f"Exported Successfully to {onnx_path}!")
