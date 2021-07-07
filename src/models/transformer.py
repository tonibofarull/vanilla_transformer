"""
Attention Is All You Need: https://arxiv.org/abs/1706.03762

Implementation of a Vanilla Transformer
"""

import torch
import torch.nn.functional as F
from torch import nn
from .modules import MultiHeadAttention, PositionalEncoding, Embedding


class Encoder(nn.Module):
    def __init__(self, d_model):
        super().__init__()
        self.mha = MultiHeadAttention(is_mask=False, d_model=d_model)
        self.drop1 = nn.Dropout(0)
        self.add_norm1 = nn.LayerNorm(d_model)
        self.fc1 = nn.Linear(d_model, 2048)
        self.fc2 = nn.Linear(2048, d_model)
        self.drop2 = nn.Dropout(0)
        self.add_norm2 = nn.LayerNorm(d_model)

    def forward(self, X, pad):
        X1 = self.mha(X, X, X, pad)
        X = self.drop1(X1)
        X = self.add_norm1(X1 + X)

        X1 = F.relu(self.fc1(X))
        X2 = self.fc2(X1)
        X2 = self.drop2(X2)
        X = self.add_norm2(X2 + X)
        return X


class Decoder(nn.Module):
    def __init__(self, d_model):
        super().__init__()
        self.mha1 = MultiHeadAttention(is_mask=True, d_model=d_model)
        self.drop1 = nn.Dropout(0)
        self.add_norm1 = nn.LayerNorm(d_model)
        self.mha2 = MultiHeadAttention(is_mask=True, d_model=d_model)
        self.drop2 = nn.Dropout(0)
        self.add_norm2 = nn.LayerNorm(d_model)
        self.fc1 = nn.Linear(d_model, 2048)
        self.fc2 = nn.Linear(2048, d_model)
        self.drop3 = nn.Dropout(0)
        self.add_norm3 = nn.LayerNorm(d_model)

    def forward(self, X, Y, pad):
        Y1 = self.mha1(Y, Y, Y, pad)
        Y1 = self.drop1(Y1)
        Y = self.add_norm1(Y1 + Y)

        Y1 = self.mha2(Y, X, X, pad)
        Y1 = self.drop2(Y1)
        Y = self.add_norm2(Y1 + Y)

        Y1 = F.relu(self.fc1(Y))
        Y2 = self.fc2(Y1)
        Y2 = self.drop3(Y2)
        Y = self.add_norm3(Y2 + Y)
        return Y


class Transformer(nn.Module):
    # def __init__(self, voc_src=13711, voc_tgt=18114, d_model=128, Nx=4):
    def __init__(self, voc_src=8, voc_tgt=7, d_model=128, Nx=6):
        super().__init__()
        self.embedding_src = Embedding(voc_src, d_model)
        self.drop1 = nn.Dropout(0)
        self.embedding_tgt = Embedding(voc_tgt, d_model)
        self.drop2 = nn.Dropout(0)
        self.pe = PositionalEncoding(d_model)
        self.encs = nn.ModuleList([Encoder(d_model) for _ in range(Nx)])
        self.decs = nn.ModuleList([Decoder(d_model) for _ in range(Nx)])
        self.fc = nn.Linear(d_model, voc_tgt)

    def forward(self, inp, out, inp_pad, out_pad):
        """
        inp: (N, L)
        out: (N, L)
        """
        # Encoder
        inp = self.embedding_src(inp)  # (N, L, d_model)
        inp = self.pe(inp)
        inp = self.drop1(inp)
        for enc in self.encs:
            inp = enc(inp, inp_pad)
        
        # Decoder
        out = self.embedding_tgt(out)  # (N, L, d_model)
        out = self.pe(out)
        out = self.drop2(out)
        for dec in self.decs:
            out = dec(inp, out, out_pad)

        # Output
        X = self.fc(out)  # (N, L, dim_out)
        X = F.softmax(X, dim=-1)
        return X
