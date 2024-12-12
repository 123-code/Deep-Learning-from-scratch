from typing import Any, Dict,List,Optional,Union,Tuple,Iterable
import numpy as np 
from PIL import Image
import torch 

IMAGENET_STANDARD_MEAN = []

def add_image_tokens_to_prompt(prefix_prompt,bos_token,image_seq_len,image_token):
    return f"{image_token * image_seq_len}{bos_token}{prefix_prompt}"

def resize(image:Image,size:Tuple[int,int],resample:Image.Resampling=None,reducing_gap:Optional[int]=None)->np.ndarray:
    height,width = size
    resized_image = image.resize((width,height),resample=resample,reducing_gap=reducing_gap)
    return resized_image



class PaliGemmaProcessor:
    image_token = "<image>"
    def __init__(self,tokenizer,num_image_tokens:int,image_size:int):
        super().__init__()
        self.image_seq_length = num_image_tokens
        self.image_size = image_size
        tokens_to_add = {"additional_special_tokens":{self.IMAGE_TOKEN}}
        tokenizer.add_special_tokens(tokens_to_add)
        EXTRA_TOKENS = [
            f"<loc{i:04d}>" for i in range(1024)
        ]
        EXTRA_TOKENS = [
            f"<seg{i:03d}>" for i in range(128)
        ]
        tokenizer.add_tokens(EXTRA_TOKENS)
        self.image_token_id = tokenizer.convert_tokens_to_ids(self.IMAGE_TOKEN)
        tokenizer.add_bos_token = False
        tokenizer.add_eos_token = False 
        self.tokenizer = tokenizer

    def __call__(
            self,
            text:List[str],
            images:List[Image,Image],
            padding:str = "longest",
            truncation:bool = True,
    )->dict:
        assert len(images) == 1 and len(text) == 1, f"received{len(images)} and{len(text)} for prompts"
        pixel_values = process_image(
            images,
            size = (self.image_size,self.image_size),
            resample = Image.Resampling.BICUBIC,
            rescale_factor = 1/255.0,
            image_mean = IMAGENET_STANDARD_MEAN,
            image_std = IMAGENET_STANDARD_STD,
        )
        pixel_values = np.stack(pixel_values,axis=0)
        pixel_values = torch.tensor(pixel_values)

        input_strings = [
            add_image_tokens_to_prompt(
                prefix_prompt=prompt,
                bos_token = self.tokenizer.bos_token,
                image_seq_len = self.image_seq_length,
                image_token = self.IMAGE_TOKEN,
            )
            for prompt in text
             
        ]

        inputs = self.tokenizer(
            input_strings,
            return_tensors="pt",
            padding = padding,
            truncation = truncation,
        )
        return_data = {"pixel_values":pixel_values,**inputs}
        return return_data