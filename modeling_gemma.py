import torch
import torch.nn as nn 
import math 
from typing import Optional,Tuple,List
from torch.nn import CrossEntropyLoss


class PaliGemmaConfig():
    def __init__(
            self,
            vision_config = None,
            text_config = None,
            ignore_index = 100,
            image_token_index = 256000,
            vocab_size = 257152,
            projection_dim = 2048,
            hidden_size = 2048,
            pad_token_id = None,
            **kwargs,
    ):
            super().__init__()
            self.ignore_index = ignore_index
            self.image_token_index = image_token_index
            self.vocab_size = vocab_size
            self.projection_dim = projection_dim
            self.hidden_size = hidden_size
            self.vision_config = vision_config
            self.is_encoder_decoder = False
            self.pad_token_id = pad_token_id





class PaliGemmaForConditionalGeneration(nn.Module):
    def __init__(self,config:PaliGemmaConfig):
        super().__init__()
        self.config = config
        self.vision_tower = SiglipVisionModel(config.vision_config)
        self.multi_modal_projector = PaliGemmaMultiModalProjector(config)
        self.vocab_size = config.vocab_size
        language_model = GemmaForCausalLM(config.text_config)
        self.language_model = language_model
        self.pad_token_id = self.config.pad_token_id if self.config.pad_token_id is not None else -1

    def tie_weights(self):
        return self.language_model.tie_weights()
    def forward(     self,input_ids:torch.LongTensor = None,
        pixel_values:torch.FloatTensor = None,
        attention_mask : Optional[torch.Tensor] = None,
        kv_cache:Optional[KVCache] = None)->Tuple:
        assert torch.all(attention_mask==1),"input cannot be padded"
        inputs_embeds = self.language_model.get_input_embeddings()(input_ids)
        selected_image_feature = self.vision_tower(pixel_values.to(inputs_embeds.dtype))
        image_features = self.multi_modal_projector(selected_image_feature)
        input_embeds,attention_mask,position_ids = self._merge_input_ids_with_image_features(image_features,inputs_embeds,input_ids,kv_cache)
        outputs = self.language_model(
            attention_mask = attention_mask
            position_ids = position_ids
            inputs_embeds = inputs_embeds
            kv_cache = kv_cache
        )
        return outputs
