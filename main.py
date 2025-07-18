# -*- coding: utf-8 -*-
"""Copie de Qwen3_(14B)-Reasoning-Conversational.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1sJlX3cPt0cg_Ii1rwRtp1WwOqdcB2TGM

To run this, press "*Runtime*" and press "*Run all*" on a **free** Tesla T4 Google Colab instance!
<div class="align-center">
<a href="https://unsloth.ai/"><img src="https://github.com/unslothai/unsloth/raw/main/images/unsloth%20new%20logo.png" width="115"></a>
<a href="https://discord.gg/unsloth"><img src="https://github.com/unslothai/unsloth/raw/main/images/Discord button.png" width="145"></a>
<a href="https://docs.unsloth.ai/"><img src="https://github.com/unslothai/unsloth/blob/main/images/documentation%20green%20button.png?raw=true" width="125"></a></a> Join Discord if you need help + ⭐ <i>Star us on <a href="https://github.com/unslothai/unsloth">Github</a> </i> ⭐
</div>

To install Unsloth on your own computer, follow the installation instructions on our Github page [here](https://docs.unsloth.ai/get-started/installing-+-updating).

You will learn how to do [data prep](#Data), how to [train](#Train), how to [run the model](#Inference), & [how to save it](#Save)

### News

Unsloth now supports Text-to-Speech (TTS) models. Read our [guide here](https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning).

Read our **[Gemma 3N Guide](https://docs.unsloth.ai/basics/gemma-3n-how-to-run-and-fine-tune)** and check out our new **[Dynamic 2.0](https://docs.unsloth.ai/basics/unsloth-dynamic-2.0-ggufs)** quants which outperforms other quantization methods!

Visit our docs for all our [model uploads](https://docs.unsloth.ai/get-started/all-our-models) and [notebooks](https://docs.unsloth.ai/get-started/unsloth-notebooks).

### Installation
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# import os
# if "COLAB_" not in "".join(os.environ.keys()):
#     !pip install unsloth
# else:
#     # Do this only in Colab notebooks! Otherwise use pip install unsloth
#     !pip install --no-deps bitsandbytes accelerate xformers==0.0.29.post3 peft trl triton cut_cross_entropy unsloth_zoo
#     !pip install sentencepiece protobuf "datasets>=3.4.1,<4.0.0" huggingface_hub hf_transfer
#     !pip install --no-deps unsloth

"""### Unsloth"""

import os
os.environ["UNSLOTH_OFFLOAD_ROPE"] = "1"  # Offload rotary embeddings to CPU
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"  # Synchronous CUDA error reporting
os.environ["TORCH_USE_CUDA_DSA"] = "1"    # Enable device-side assertions
os.environ["NVIDIA_DEBUG"] = "1"          # NVIDIA driver debug info

# Force FP32 precision for compatibility
os.environ["UNSLOTH_FORCE_FP32"] = "1"

# Disable xFormers explicitly
os.environ["XFORMERS_DISABLED"] = "1"

# Set broader CUDA architecture compatibility
os.environ["TORCH_CUDA_ARCH_LIST"] = "sm_90;sm_89;sm_86;sm_80;sm_75"

# Verify environment
print("="*50)
print("ENVIRONMENT CONFIGURATION:")
print(f"UNSLOTH_OFFLOAD_ROPE: {os.getenv('UNSLOTH_OFFLOAD_ROPE')}")
print(f"UNSLOTH_FORCE_FP32: {os.getenv('UNSLOTH_FORCE_FP32')}")
print(f"XFORMERS_DISABLED: {os.getenv('XFORMERS_DISABLED')}")
print(f"TORCH_CUDA_ARCH_LIST: {os.getenv('TORCH_CUDA_ARCH_LIST')}")
print("="*50)

# Additional diagnostics
import torch
print("\nTORCH/CUDA STATUS:")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
    print(f"Device capability: {torch.cuda.get_device_capability(0)}")
    print(f"CUDA arch list: {torch.cuda.get_arch_list()}")
print("="*50)

# Rest of your imports...
from unsloth import FastLanguageModel

# Rest of your imports below
from unsloth import FastLanguageModel

# After imports
print("\nGPU STATUS:")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
    print(f"Device capability: {torch.cuda.get_device_capability(0)}")
    print(f"PyTorch CUDA version: {torch.version.cuda}")


fourbit_models = [
    "unsloth/Qwen3-1.7B-unsloth-bnb-4bit", # Qwen 14B 2x faster
    "unsloth/Qwen3-4B-unsloth-bnb-4bit",
    "unsloth/Qwen3-8B-unsloth-bnb-4bit",
    "unsloth/Qwen3-14B-unsloth-bnb-4bit",
    "unsloth/Qwen3-32B-unsloth-bnb-4bit",

    # 4bit dynamic quants for superior accuracy and low memory use
    "unsloth/gemma-3-12b-it-unsloth-bnb-4bit",
    "unsloth/Phi-4",
    "unsloth/Llama-3.1-8B",
    "unsloth/Llama-3.2-3B",
    "unsloth/orpheus-3b-0.1-ft-unsloth-bnb-4bit" # [NEW] We support TTS models!
] # More models at https://huggingface.co/unsloth

model, tokenizer = FastLanguageModel.from_pretrained(
  model_name = "unsloth/Qwen3-1.7B-unsloth-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)

"""We now add LoRA adapters so we only need to update 1 to 10% of all parameters!"""

model = FastLanguageModel.get_peft_model(
    model,
    r = 32,           # Choose any number > 0! Suggested 8, 16, 32, 64, 128
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 32,  # Best to choose alpha = rank or rank*2
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    use_rslora = False,   # We support rank stabilized LoRA
    loftq_config = None,  # And LoftQ
)

"""<a name="Data"></a>
### Data Prep
Qwen3 has both reasoning and a non reasoning mode. So, we should use 2 datasets:

1. We use the [Open Math Reasoning]() dataset which was used to win the [AIMO](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-2/leaderboard) (AI Mathematical Olympiad - Progress Prize 2) challenge! We sample 10% of verifiable reasoning traces that used DeepSeek R1, and whicht got > 95% accuracy.

2. We also leverage [Maxime Labonne's FineTome-100k](https://huggingface.co/datasets/mlabonne/FineTome-100k) dataset in ShareGPT style. But we need to convert it to HuggingFace's normal multiturn format as well.
"""

from datasets import load_dataset
reasoning_dataset = load_dataset("csv", data_files="./qa_dataset_ollama.csv", split="train")
non_reasoning_dataset = load_dataset("mlabonne/FineTome-100k", split = "train")

"""Let's see the structure of both datasets:"""

reasoning_dataset

non_reasoning_dataset

"""We now convert the reasoning dataset into conversational format:"""

def generate_conversation(examples):
    problems  = examples["problem"]
    solutions = examples["generated_solution"]
    conversations = []
    for problem, solution in zip(problems, solutions):
        conversations.append([
            {"role" : "user",      "content" : problem},
            {"role" : "assistant", "content" : solution},
        ])
    return { "conversations": conversations, }

reasoning_conversations = tokenizer.apply_chat_template(
    reasoning_dataset.map(generate_conversation, batched = True)["conversations"],
    tokenize = False,
)

"""Let's see the first transformed row:"""

reasoning_conversations[0]

"""Next we take the non reasoning dataset and convert it to conversational format as well.

We have to use Unsloth's `standardize_sharegpt` function to fix up the format of the dataset first.
"""

from unsloth.chat_templates import standardize_sharegpt
dataset = standardize_sharegpt(non_reasoning_dataset)

non_reasoning_conversations = tokenizer.apply_chat_template(
    dataset["conversations"],
    tokenize = False,
)

"""Let's see the first row"""

non_reasoning_conversations[0]

"""Now let's see how long both datasets are:"""

print(len(reasoning_conversations))
print(len(non_reasoning_conversations))

"""The non reasoning dataset is much longer. Let's assume we want the model to retain some reasoning capabilities, but we specifically want a chat model.

Let's define a ratio of chat only data. The goal is to define some mixture of both sets of data.

Let's select 75% reasoning and 25% chat based:
"""

chat_percentage = 0.25

"""Let's sample the reasoning dataset by 75% (or whatever is 100% - chat_percentage)"""

import pandas as pd
non_reasoning_subset = pd.Series(non_reasoning_conversations)
non_reasoning_subset = non_reasoning_subset.sample(
    int(len(reasoning_conversations)*(chat_percentage/(1 - chat_percentage))),
    random_state = 2407,
)
print(len(reasoning_conversations))
print(len(non_reasoning_subset))
print(len(non_reasoning_subset) / (len(non_reasoning_subset) + len(reasoning_conversations)))

"""Finally combine both datasets:"""

data = pd.concat([
    pd.Series(reasoning_conversations),
    pd.Series(non_reasoning_subset)
])
data.name = "text"

from datasets import Dataset
combined_dataset = Dataset.from_pandas(pd.DataFrame(data))
combined_dataset = combined_dataset.shuffle(seed = 3407)

"""<a name="Train"></a>
### Train the model
Now let's use Huggingface TRL's `SFTTrainer`! More docs here: [TRL SFT docs](https://huggingface.co/docs/trl/sft_trainer). We do 60 steps to speed things up, but you can set `num_train_epochs=1` for a full run, and turn off `max_steps=None`.
"""

from trl import SFTTrainer, SFTConfig
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = combined_dataset,
    eval_dataset = None, # Can set up evaluation!
    args = SFTConfig(
        dataset_text_field = "text",
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4, # Use GA to mimic batch size!
        warmup_steps = 5,
        # num_train_epochs = 1, # Set this for 1 full training run.
        max_steps = 30,
        learning_rate = 2e-4, # Reduce to 2e-5 for long training runs
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        report_to = "none", # Use this for WandB etc
    ),
)

# @title Show current memory stats
gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
print(f"{start_gpu_memory} GB of memory reserved.")

"""Let's train the model! To resume a training run, set `trainer.train(resume_from_checkpoint = True)`"""

trainer_stats = trainer.train()

# @title Show final memory and time stats
used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
used_percentage = round(used_memory / max_memory * 100, 3)
lora_percentage = round(used_memory_for_lora / max_memory * 100, 3)
print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
print(
    f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training."
)
print(f"Peak reserved memory = {used_memory} GB.")
print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
print(f"Peak reserved memory % of max memory = {used_percentage} %.")
print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")

"""<a name="Inference"></a>
### Inference
Let's run the model via Unsloth native inference! According to the `Qwen-3` team, the recommended settings for reasoning inference are `temperature = 0.6, top_p = 0.95, top_k = 20`

For normal chat based inference, `temperature = 0.7, top_p = 0.8, top_k = 20`
"""

messages = [
    {"role" : "user", "content" : "Can you provide a detailed description of the directory structure, including all subdirectories, configuration files, and artifacts, generated by the abp generate-proxy command in an ABP.IO project?"}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize = False,
    add_generation_prompt = True, # Must add for generation
    enable_thinking = False, # Disable thinking
)

from transformers import TextStreamer
_ = model.generate(
    **tokenizer(text, return_tensors = "pt").to("cuda"),
    max_new_tokens = 256, # Increase for longer outputs!
    temperature = 0.7, top_p = 0.8, top_k = 20, # For non thinking
    streamer = TextStreamer(tokenizer, skip_prompt = True),
)

messages = [
    {"role" : "user", "content" : "Can you provide a detailed description of the directory structure, including all subdirectories, configuration files, and artifacts, generated by the abp generate-proxy command in an ABP.IO project?"}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize = False,
    add_generation_prompt = True, # Must add for generation
    enable_thinking = True, # Disable thinking
)

from transformers import TextStreamer
_ = model.generate(
    **tokenizer(text, return_tensors = "pt").to("cuda"),
    max_new_tokens = 1024, # Increase for longer outputs!
    temperature = 0.6, top_p = 0.95, top_k = 20, # For thinking
    streamer = TextStreamer(tokenizer, skip_prompt = True),
)

"""<a name="Save"></a>
### Saving, loading finetuned models
To save the final model as LoRA adapters, either use Huggingface's `push_to_hub` for an online save or `save_pretrained` for a local save.

**[NOTE]** This ONLY saves the LoRA adapters, and not the full model. To save to 16bit or GGUF, scroll down!
"""

model.save_pretrained("lora_model")  # Local saving
tokenizer.save_pretrained("lora_model")
model.push_to_hub("bzouiri/bzfirstmodel", token="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")
tokenizer.push_to_hub("bzouiri/bzfirstmodel", token="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")

"""Now if you want to load the LoRA adapters we just saved for inference, set `False` to `True`:"""

if False:
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "lora_model", # YOUR MODEL YOU USED FOR TRAINING
        max_seq_length = 2048,
        load_in_4bit = True,
    )

"""### Saving to float16 for VLLM

We also support saving to `float16` directly. Select `merged_16bit` for float16 or `merged_4bit` for int4. We also allow `lora` adapters as a fallback. Use `push_to_hub_merged` to upload to your Hugging Face account! You can go to https://huggingface.co/settings/tokens for your personal tokens.
"""

# Fusionner les poids LoRA avec le modèle de base (nécessaire pour VLLM)
model = model.merge_and_unload()  # Fusionne et décharge les adaptateurs

# Sauvegarde locale au format 16-bit (recommandé pour VLLM)
model.save_pretrained("vllm_model", torch_dtype=torch.float16)
tokenizer.save_pretrained("vllm_model")

# Envoi vers le Hub Hugging Face
model.push_to_hub(
    "bzouiri/bzfirstmodel",
    token="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",
    revision="vllm-16bit",  # Spécifie une révision
    torch_dtype=torch.float16
)
tokenizer.push_to_hub(
    "bzouiri/bzfirstmodel",
    token="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",
    revision="vllm-16bit"
)

"""### GGUF / llama.cpp Conversion
To save to `GGUF` / `llama.cpp`, we support it natively now! We clone `llama.cpp` and we default save it to `q8_0`. We allow all methods like `q4_k_m`. Use `save_pretrained_gguf` for local saving and `push_to_hub_gguf` for uploading to HF.

Some supported quant methods (full list on our [Wiki page](https://github.com/unslothai/unsloth/wiki#gguf-quantization-options)):
* `q8_0` - Fast conversion. High resource use, but generally acceptable.
* `q4_k_m` - Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q4_K.
* `q5_k_m` - Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q5_K.

[**NEW**] To finetune and auto export to Ollama, try our [Ollama notebook](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3_(8B)-Ollama.ipynb)
"""

from huggingface_hub import HfApi, create_repo
from ctransformers import AutoModelForCausalLM
import os

# Initialisation
api = HfApi(token="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")
repo_id = "bzouiri/bzfirstmodel"
create_repo(repo_id, token=api.token, exist_ok=True)

# Fusion du modèle
model = model.merge_and_unload()

# Conversion et upload
quant_methods = ["q4_k_m", "q8_0", "f16"]  # f16 = 16-bit non quantifié

for method in quant_methods:
    try:
        # Conversion GGUF
        gguf_model = AutoModelForCausalLM.from_pretrained(
            model,
            model_type="auto",
            lib="avx2",
            quantization=method if method != "f16" else None
        )

        # Nom du fichier
        filename = f"bzfirstmodel_{method}.gguf"
        gguf_model.save(filename)

        # Upload vers HF Hub
        api.upload_file(
            repo_id=repo_id,
            path_in_repo=filename,
            path_or_fileobj=filename
        )
        print(f"✅ Fichier {filename} uploadé avec succès!")

        # Nettoyage
        os.remove(filename)

    except Exception as e:
        print(f"❌ Erreur pour {method}: {str(e)}")

"""Now, use the `model-unsloth.gguf` file or `model-unsloth-Q4_K_M.gguf` file in llama.cpp or a UI based system like Jan or Open WebUI. You can install Jan [here](https://github.com/janhq/jan) and Open WebUI [here](https://github.com/open-webui/open-webui)

And we're done! If you have any questions on Unsloth, we have a [Discord](https://discord.gg/unsloth) channel! If you find any bugs or want to keep updated with the latest LLM stuff, or need help, join projects etc, feel free to join our Discord!

Some other links:
1. Train your own reasoning model - Llama GRPO notebook [Free Colab](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3.1_(8B)-GRPO.ipynb)
2. Saving finetunes to Ollama. [Free notebook](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3_(8B)-Ollama.ipynb)
3. Llama 3.2 Vision finetuning - Radiography use case. [Free Colab](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3.2_(11B)-Vision.ipynb)
6. See notebooks for DPO, ORPO, Continued pretraining, conversational finetuning and more on our [documentation](https://docs.unsloth.ai/get-started/unsloth-notebooks)!

<div class="align-center">
  <a href="https://unsloth.ai"><img src="https://github.com/unslothai/unsloth/raw/main/images/unsloth%20new%20logo.png" width="115"></a>
  <a href="https://discord.gg/unsloth"><img src="https://github.com/unslothai/unsloth/raw/main/images/Discord.png" width="145"></a>
  <a href="https://docs.unsloth.ai/"><img src="https://github.com/unslothai/unsloth/blob/main/images/documentation%20green%20button.png?raw=true" width="125"></a>

  Join Discord if you need help + ⭐️ <i>Star us on <a href="https://github.com/unslothai/unsloth">Github</a> </i> ⭐️
</div>

"""