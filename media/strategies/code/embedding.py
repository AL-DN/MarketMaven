# Author: Alden Sahi
# Date: 10/04/2025
# Program Description: Allows for convient embedding generation ( pass in model name into class and functions are ready to go )

from typing import Union
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

class EmbeddingModel():
    """Abstract base class for embedding models using their own tokenizer"""
    
    def __init__(self, model_name:str):
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name must be a non-empty string")
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def eval(self):
        """Prints Model Architecture"""
        print(self.model.eval())
        
    def get_token_ids(self, text: Union[str, list[str]]) -> torch.Tensor:
        return self.tokenizer(text, padding=True, truncation=True, max_length=64, return_tensors="pt")
    
    def contextualize_token_ids(self, enc: dict[str,torch.Tensor]) -> torch.Tensor:
        """Generate Embeddings For Tokens
            rtype: Tensor -shape = [1, sequence_length, hidden_dim] contains real and pad tokens msak for model is only for attention mechanism"""
        
        input_ids = enc['input_ids']
        attention_mask = enc['attention_mask']
        
        #makes context aware embeddings from tensors
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            hidden = outputs.last_hidden_state
            
        return hidden, attention_mask
    
    def select_embedding_type(self, type: str, hidden:torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """ Selects embedding type and adjusts attention mask to se disparities in evaluation."""
        # if hidden.shape.len() != 3:
        #     raise ValueError(f"Expected 3D tensor, got {hidden.dim()}D")
        
        if type == "cls":
            embedding = hidden[:,0,:]
            mask = attention_mask[:,0:1]
        elif type == "w_cls":
            embedding = hidden
            mask = attention_mask
        elif type == "wo_cls":
            embedding = hidden[:, 1: ,:]
            mask = attention_mask[:, 1:]
        else:
            raise ValueError('Not a Valid Embedding Type')
    

        return embedding, mask
    
    def calculate_v1(self, strat: str, hidden: torch.Tensor, attention_mask: torch.Tensor, is_cls: bool) -> torch.Tensor:
        
        if is_cls: 
            #print("Returning Original CLS from calculate_v1. ")
            return hidden
    
        if strat == 'mean':
            mask = attention_mask.unsqueeze(-1).expand(hidden.size())
            summed = torch.sum(hidden * mask, dim=1) # shape: [1,768]
            counts = torch.clamp(attention_mask.sum(dim=1, keepdim=True), min=1)
            query_vec = (summed / counts)
           
        
        elif strat == "max":
            # handles negative embedding edge case (is it even possible?)
            mask = attention_mask.unsqueeze(-1).expand(hidden.size())
            
            # apply mask to hidden + find max vector
            masked_hidden = hidden.clone()
            masked_hidden[mask == 0] = -torch.inf
            query_vec, _ = torch.max(masked_hidden, dim=1) # sum for each dim across all embeddings
        else:
            raise ValueError('Not a Valid Embedding Strategy')
    
            
        return query_vec                           
        
    def embed_text(self, text: Union[str, list[str]], embedding_type: str, strat: str, verbose: bool = False)-> torch.Tensor:
        """Convience Method to tokenize and embed in one class"""
        token_ids = self.get_token_ids(text)
        hidden, attention_mask = self.contextualize_token_ids(token_ids)
        hidden, attention_mask = self.select_embedding_type(
            type=embedding_type,
            hidden=hidden,
            attention_mask=attention_mask
        )
        
        v1 =  self.calculate_v1(
            strat=strat,
            is_cls=(embedding_type == "cls"),
            hidden=hidden,
            attention_mask=attention_mask)
        
        
        if verbose:
            print("=" * 60)
            print("EMBEDDING PIPELINE DEBUG INFO")
            print("=" * 60)
            
            # Input info
            if isinstance(text, str):
                print(f"Input text: '{text}'")
                print(f"Input type: single string")
            else:
                print(f"Input texts: {len(text)} strings")
                print(f"Sample: '{text[0][:50]}{'...' if len(text[0]) > 50 else ''}'")
            
            # Tokenization info
            print(f"\n--- Tokenization ---")
            if isinstance(token_ids, torch.Tensor):
                print(f"Token IDs shape: {tuple(token_ids.shape)}")
                if token_ids.dim() == 1:
                    print(f"Token IDs: {token_ids.tolist()}")
                else:
                    print(f"Token IDs sample (first sequence): {token_ids[0].tolist()}")
        
            # Contextualization info
            print(f"\n--- Contextualization ---")
            print(f"Hidden states shape: {tuple(hidden.shape)}")
            print(f"Attention mask shape: {tuple(attention_mask.shape)}")
            
            # Embedding type selection
            print(f"\n--- Embedding Type Selection ---")
            print(f"Selected type: {embedding_type}")
            print(f"Hidden states after selection: {tuple(hidden.shape)}")
            
            # Final embedding calculation
            print(f"\n--- Final Embedding ---")
            print(f"Strategy: {strat}")
            print(f"Output embedding shape: {tuple(v1.shape)}")
            print(f"Output dtype: {v1.dtype}")
            print(f"Device: {v1.device}")
            
            # Show sample values
            print(f"\n--- Sample Values ---")
            if v1.dim() == 1:
                print(f"First 5 values: {v1[:5].tolist()}")
                print(f"Embedding norm: {torch.norm(v1):.4f}")
            elif v1.dim() == 2:
                print(f"First embedding first 5 values: {v1[0][:5].tolist()}")
                print(f"First embedding norm: {torch.norm(v1[0]):.4f}")
                if v1.shape[0] > 1:
                    print(f"Second embedding first 5 values: {v1[1][:5].tolist()}")
            
            print("=" * 60)
        
        return v1
    