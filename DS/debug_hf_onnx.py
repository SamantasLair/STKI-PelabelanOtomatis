import os
from pathlib import Path
from transformers import AutoTokenizer
from transformers.onnx import export, FeaturesManager

print('Loading model and exporting via HF transformers.onnx...')
checkpoint_path = './results/checkpoint-800'
original_model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

tokenizer = AutoTokenizer.from_pretrained(original_model_name)

# Using transformers.onnx.export handles all tracing bugs internally!
onnx_path = Path('./onnx_model/multi_label_model.onnx')
onnx_path.parent.mkdir(parents=True, exist_ok=True)

# Generate config for feature extraction
_, model_onnx_config = FeaturesManager.check_supported_model_or_raise(
    model=None, 
    feature='default', 
    model_type='bert'
)
onnx_config = model_onnx_config(None)

try:
    from transformers import AutoModel
    model = AutoModel.from_pretrained(checkpoint_path)
    export(
        preprocessor=tokenizer,
        model=model,
        config=onnx_config,
        opset=14,
        output=onnx_path
    )
    print('SUCCESS')
except Exception as e:
    import traceback
    traceback.print_exc()
