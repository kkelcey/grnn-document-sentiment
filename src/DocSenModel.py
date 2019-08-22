import torch
from torch.utils.data import sampler, DataLoader

import numpy as np

from src.ImdbDataset import ImdbDataset

from typing import Dict

from src.DocSenTypes import *
from src.DocumentPadCollate import DocumentPadCollate


class DocSenModel(torch.nn.Module):
    def __init__(self, embedding_matrix: np.array, word2idx: Dict[TWord, TVocabIndex], freeze_embedding: bool = True):
        super(DocSenModel, self).__init__()

        self._word_embedding_dim = len(embedding_matrix[0])
        self._vocab_size = len(embedding_matrix)

        # Call: embed(torch.from_numpy(np.array([id1, id2, ..., idn])))
        #  => n-dim embedding vector of words with given vocab ids
        self._word_embedding = torch.nn.Embedding.from_pretrained(torch.from_numpy(embedding_matrix), freeze=freeze_embedding)

    def forward(self, X):
        X = self._word_embedding(X)
        # torch.nn.utils.rnn.pack_padded_sequence(X, X_lengths, batch_first=True)
        return X


if __name__ == '__main__':
    num_epochs = 10
    w2v_sample_frac = 0.9
    data_path = 'data/Dev/imdb-dev.txt.ss'
    data_name = 'imdb-dev'
    freeze_embedding = True
    batch_size = 16
    validation_split = 0.2
    shuffle_dataset = False
    random_seed = 42
    learning_rate = 0.03

    dataset = ImdbDataset(data_path, data_name, w2v_sample_frac=w2v_sample_frac)

    model = DocSenModel(dataset.embedding, dataset.word2index, freeze_embedding=freeze_embedding)

    dataset_size = len(dataset)
    indices = list(range(dataset_size))
    split = int(np.floor(validation_split * dataset_size))
    if shuffle_dataset:
        np.random.seed(random_seed)
        np.random.shuffle(indices)
    train_indices, val_indices = indices[split:], indices[:split]

    train_sampler = sampler.SubsetRandomSampler(train_indices)
    valid_sampler = sampler.SubsetRandomSampler(val_indices)

    # DataLoader srews up the data if they are of varying length.
    # Like our data: documents have varying number of sentences and sentences have varying number of words.
    # Thus we need to use a custom collate function that pads the documents' sentence lists and every sentence's word
    # list before the document tensors get stacked.
    pad_collate_fn = DocumentPadCollate(dataset.word2index[dataset.padding_word_key])
    train_loader = DataLoader(dataset, batch_size=batch_size, sampler=train_sampler, collate_fn=pad_collate_fn)
    validation_loader = DataLoader(dataset, batch_size=batch_size, sampler=valid_sampler, collate_fn=pad_collate_fn)

    loss_function = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    learning_curve = []
    for epoch in range(num_epochs):
        print(f'\nEpoch {epoch}')
        for batch_index, (documents, labels) in enumerate(train_loader):
            # for i, doc in enumerate(documents):
            print(f'Batch {batch_index}: {labels}, {len(documents)}')

            # apply the model with the current parameters
            label_predicted = model(documents)

            # compute the loss and store it; note that the loss is an object
            # which we will also need to compute the gradient
            # loss_object = loss_function(labels[i], label_predicted)
            # learning_curve.append(loss_object.item())
            #
            # # print the loss every 50 steps so that we see the progress
            # # while learning happens
            # if len(learning_curve) % 50 == 0:
            #     print('loss after {} steps: {}'.format(len(learning_curve), learning_curve[-1]))
            #
            # # A special feature of PyTorch is that we need to zero the gradients
            # # in the optimizer to ensure that past computations do
            # # not influence the present ones
            # optimizer.zero_grad()
            #
            # # compute the gradient of the loss
            # loss_object.backward()
            #
            # # compute a step of the optimizer based on the gradient
            # optimizer.step()
