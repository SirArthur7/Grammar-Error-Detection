# -*- coding: utf-8 -*-
"""GED_SHL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fZJx2kRQGb8hGQLeFpUrP9JX1lDLgGiW

# Installing packages and using GPU
"""

import torch

# If there's a GPU available...
if torch.cuda.is_available():    

    # Tell PyTorch to use the GPU.    
    device = torch.device("cuda")

    print('There are %d GPU(s) available.' % torch.cuda.device_count())

    print('We will use the GPU:', torch.cuda.get_device_name(0))

# If not...
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

!pip install git+https://github.com/huggingface/transformers
!pip install tqdm

"""# Data Pre-processing and Dataset Loaders"""

# importing required libraries and modules
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from sklearn.metrics import confusion_matrix, f1_score, precision_score
from tqdm import tqdm

# defining the class for DebertaDataset
class DebertaDataset:
    def __init__(self, sentences, labels=None, tokenizer_name='sileod/deberta-v3-base-tasksource-nli', batch_size=16):
        # instantiating a tokenizer object
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.batch_size = batch_size
        
        # creating input ids, attention masks and labels for the given sentences
        self.input_ids, self.attention_masks, self.labels = self._prepare_data(sentences, labels)
        
        # creating dataloaders for training, validation and testing
        self.train_dataloader = self._create_train_dataloader()
        self.val_dataloader = self._create_val_dataloader()
        self.test_dataloader = self._create_test_dataloader()

    # method to prepare data for DebertaClassifier
    def _prepare_data(self, sentences, labels):
        input_ids = []
        attention_masks = []
        
        # convert labels into tensor objects, if not None
        if labels is not None:
            labels = torch.tensor(labels)

        # loop through the sentences, tokenize and create input ids, attention masks
        for sent in sentences:
            encoded_dict = self.tokenizer.encode_plus(
                sent,                      # Sentence to encode.
                add_special_tokens=True,   # Add '[CLS]' and '[SEP]'
                max_length=128,           # Pad & truncate all sentences.
                pad_to_max_length=True,
                return_attention_mask=True,   # Construct attn. masks.
                return_tensors='pt',     # Return pytorch tensors.
            )
            input_ids.append(encoded_dict['input_ids'])
            attention_masks.append(encoded_dict['attention_mask'])

        # concatenate the list of input ids and attention masks into tensors
        input_ids = torch.cat(input_ids, dim=0)
        attention_masks = torch.cat(attention_masks, dim=0)
        
        # create a tensor object for labels, if None
        if labels is None:
            labels = torch.zeros(len(sentences), dtype=torch.long)

        return input_ids, attention_masks, labels

    # method to create dataloader for training
    def _create_train_dataloader(self):
        # create dataset from input ids, attention masks and labels
        dataset = TensorDataset(self.input_ids, self.attention_masks, self.labels)

        # create dataloader with random sampler
        dataloader = DataLoader(
            dataset,  # The samples.
            sampler=RandomSampler(dataset), # Select batches randomly
            batch_size=self.batch_size # Trains with this batch size.
        )

        return dataloader
    
    # method to create dataloader for validation
    def _create_val_dataloader(self):
        # create dataset from input ids, attention masks and labels
        dataset = TensorDataset(self.input_ids, self.attention_masks, self.labels)

        # create dataloader with sequential sampler
        dataloader = DataLoader(
            dataset,  # The samples.
            sampler=SequentialSampler(dataset), # Select batches sequentially
            batch_size=self.batch_size # Validates with this batch size.
        )

        return dataloader
    
    # method to create dataloader for testing
    def _create_test_dataloader(self):
        # create dataset from input ids and attention masks
        dataset = TensorDataset(self.input_ids, self.attention_masks)

        dataloader = DataLoader(
            dataset,  # The samples.
            sampler=SequentialSampler(dataset), # Select batches sequentially
            batch_size=self.batch_size # Tests with this batch size.
        )

        return dataloader

"""References"""

# @article{sileo2023tasksource,
#   title={tasksource: Structured Dataset Preprocessing Annotations for Frictionless Extreme Multi-Task Learning and Evaluation},
#   author={Sileo, Damien},
#   url= {https://arxiv.org/abs/2301.05948},
#   journal={arXiv preprint arXiv:2301.05948},
#   year={2023}
# }

"""# DeBERTaV3 + CNN Classifier Model"""

import torch.nn as nn
from transformers import AutoModel

num_classes = 2

# Define a class DebertaClassifier that inherits from nn.Module
class DebertaClassifier(nn.Module):
    # Constructor method for the DebertaClassifier class
    def __init__(self, num_classes):
        # Call the constructor of the superclass (nn.Module)
        super(DebertaClassifier, self).__init__()
        # Load the pre-trained DeBERTa model
        self.deberta = AutoModel.from_pretrained('yevheniimaslov/deberta-v3-base-cola')
        # Define a dropout layer with 10% dropout probability
        self.dropout = nn.Dropout(0.1)
        # Define a 1D convolutional layer with 768 input channels, 256 output channels, and kernel size 3
        self.conv1d = nn.Conv1d(in_channels=768, out_channels=256, kernel_size=3, padding=1)        
        # Define a ReLU activation function
        self.relu = nn.ReLU()
        # Define an adaptive max pooling layer with output size 1
        self.pooling = nn.AdaptiveMaxPool1d(1)
        # Define a fully connected (linear) layer with 256 input features and num_classes output features
        self.fc1 = nn.Linear(256, num_classes)
        # Define a softmax activation function
        self.softmax = nn.Softmax(dim=1)
        
    # Define the forward method for the DebertaClassifier class
    def forward(self, input_ids, attention_mask, token_type_ids=None, labels=None):
        # Pass the input through the DeBERTa model and obtain the last hidden state
        outputs = self.deberta(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        last_hidden_state = outputs.last_hidden_state
        # Transpose the last hidden state so that the channels dimension comes second
        last_hidden_state = last_hidden_state.transpose(1,2)
        # Apply dropout to the last hidden state
        x = self.dropout(last_hidden_state)
        # Apply the 1D convolutional layer to the last hidden state
        x = self.conv1d(x)
        # Apply the ReLU activation function to the output of the convolutional layer
        x = self.relu(x)
        # Apply the adaptive max pooling layer to the output of the ReLU activation function
        x = self.pooling(x).squeeze()
        # Apply the fully connected layer to the output of the adaptive max pooling layer
        x = self.fc1(x)
        # Apply the softmax activation function to the output of the fully connected layer
        x = self.softmax(x)
        # Create a tuple of outputs containing the predicted class probabilities
        outputs = (x,)
        # If labels are provided, calculate the cross-entropy loss and add it to the outputs tuple
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(x.view(-1, num_classes), labels.view(-1))
            outputs = (loss,) + outputs
        
        return outputs

"""# Training Validation and Testing"""

# Import necessary libraries
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from sklearn.metrics import confusion_matrix, f1_score, precision_score
from tqdm import tqdm
import csv

class DebertaTrainer:
    def __init__(self, dataset_train, dataset_val, dataset_test, num_classes=2, learning_rate=2e-5, eps=1e-8, weight_decay=0.01, betas=(0.9, 0.999), num_epochs=2, warmup_prop=0.1):
        # Initialize DebertaClassifier model with specified number of classes
        self.model = DebertaClassifier(num_classes)
        # Send the model to the GPU if available
        self.model.cuda()
        # Initialize hyperparameters
        self.learning_rate = learning_rate
        self.eps = eps
        self.weight_decay = weight_decay
        self.betas = betas
        self.num_epochs = num_epochs
        self.warmup_prop = warmup_prop
        
        # Create dataloaders for train, validation, and test datasets
        self.train_dataloader = dataset_train.train_dataloader
        self.validation_dataloader = dataset_val.val_dataloader
        self.test_dataloader = dataset_test.test_dataloader

        # Initialize optimizer and scheduler
        self.optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, eps=self.eps, weight_decay=self.weight_decay, betas=self.betas)
        self.scheduler = get_linear_schedule_with_warmup(self.optimizer, num_warmup_steps=len(self.train_dataloader) * self.num_epochs * self.warmup_prop, num_training_steps=len(self.train_dataloader) * self.num_epochs)

    # This function is used to train the model for one epoch
    def _train_epoch(self, epoch):
        # Set the model to training mode
        self.model.train()
        
        # Initialize variables for tracking training progress
        train_loss = 0
        train_f1 = 0
        train_precision = 0
        num_train_steps = 0
        
        # Get an iterator for the training data
        train_iterator = tqdm(self.train_dataloader, desc="Training")
        
        # Loop over each batch in the training data
        for step, batch in enumerate(train_iterator):
            # Extract the input_ids, attention_masks, and labels from the batch
            input_ids = batch[0].to(device)
            attention_masks = batch[1].to(device)
            labels = batch[2].to(device)

            # Clear the gradients
            self.model.zero_grad()
            
            # Forward pass through the model and calculate the loss and logits
            loss, logits = self.model(input_ids, attention_mask=attention_masks, labels=labels)
            
            # Backpropagate the loss
            loss.backward()

            # Clip the gradients to avoid exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            
            # Update the model parameters using the optimizer
            self.optimizer.step()
            
            # Adjust the learning rate using the scheduler
            self.scheduler.step()

            # Update the training loss, F1 score, and precision for this batch
            train_loss += loss.item()
            train_f1 += f1_score(torch.argmax(logits, axis=1).cpu().numpy(), labels.cpu().numpy(), average='macro')
            train_precision += precision_score(torch.argmax(logits, axis=1).cpu().numpy(), labels.cpu().numpy(), average='macro')
            
            # Increment the number of training steps
            num_train_steps += 1
            
            # Update the progress bar with the current epoch and training loss
            train_iterator.set_description(f"Epoch {epoch+1} - Train loss: {train_loss/num_train_steps:.3f}")

        # Calculate the average training loss, F1 score, and precision over all training steps
        train_loss /= num_train_steps
        train_f1 /= num_train_steps
        train_precision /= num_train_steps

        # Print the average training loss, F1 score, and precision for this epoch
        print(f"Epoch {epoch+1} - Training loss: {train_loss:.3f}, Training F1 score: {train_f1:.3f}, Training Precision: {train_precision:.3f}")

    # Define a method for validation
    def evaluate(self):
        # Set the model in evaluation mode
        self.model.eval()
        # Initialize variables for evaluation metrics
        val_loss = 0
        val_f1 = 0
        val_precision = 0
        num_val_steps = 0
        # Initialize lists for collecting all predictions and labels for confusion matrix
        all_predictions = []
        all_labels = []

        # Iterate over the validation data loader
        for batch in tqdm(self.validation_dataloader, desc="Validation"):
            # Extract input_ids, attention_masks, and labels from the batch and send them to device (CPU/GPU)
            input_ids = batch[0].to(device)
            attention_masks = batch[1].to(device)
            labels = batch[2].to(device)

            # Disable gradient computation
            with torch.no_grad():
                # Get the loss and logits from the model
                loss, logits = self.model(input_ids, attention_mask=attention_masks, labels=labels)

            # Update the loss and evaluation metrics
            val_loss += loss.item()
            # Compute F1 score for validation set by taking the argmax of the logits and comparing them to the labels
            val_f1 += f1_score(torch.argmax(logits, axis=1).cpu().numpy(), labels.cpu().numpy(), average='macro')
            # Compute Precision score for validation set by taking the argmax of the logits and comparing them to the labels
            val_precision += precision_score(torch.argmax(logits, axis=1).cpu().numpy(), labels.cpu().numpy(), average='macro')
            num_val_steps += 1

            # Collect all predictions and labels for confusion matrix
            all_predictions.extend(torch.argmax(logits, axis=1).cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

        # Compute the average validation loss and evaluation metrics
        val_loss /= num_val_steps
        val_f1 /= num_val_steps
        val_precision /= num_val_steps
        # Compute confusion matrix for the validation set using all the predictions and labels
        cm = confusion_matrix(all_labels, all_predictions)

        # Return the validation loss, F1 score, Precision score, and confusion matrix
        return (val_loss, val_f1, val_precision, cm)

    # Define a method for training
    def train(self):
        # Set the initial best validation loss to infinity
        best_val_loss = float('inf')
        # Iterate over the number of epochs
        for epoch in range(self.num_epochs):
            # Call the train_epoch method to train the model for one epoch
            self._train_epoch(epoch)

            # Evaluate the model on the validation set
            val_loss, val_f1, val_precision, confusion_matrix = self.evaluate()

            # Save the model if the validation loss has improved
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                # Save the state dict of the model to a file named 'model.pt'
                torch.save(self.model.state_dict(), "model.pt")
                # Print a message indicating that the model has been saved and the epoch number
                print(f"Saved model at epoch {epoch + 1}:")

            # Print the epoch number, validation loss, F1 score, Precision score, and confusion matrix
            print(f"Epoch {epoch + 1}:")
            print(f"Validation loss: {val_loss:.3f}, Validation F1 score: {val_f1:.3f}, Validation Precision: {val_precision:.3f}")
            print(f"Confusion matrix:\n{confusion_matrix}")

    # Define a method for training
    def test(self):
        # Load saved model from .pt file
        self.model.load_state_dict(torch.load("model.pt"))
        self.model.eval()

        # Predict labels for test sentences
        predictions = []
        for batch in tqdm(self.test_dataloader, desc="Testing"):
            # Get input IDs and attention masks for current batch and move to device
            input_ids = batch[0].to(device)
            attention_masks = batch[1].to(device)

            # Disable gradient computation
            with torch.no_grad():
                # Forward pass through the model
                logits, = self.model(input_ids, attention_mask=attention_masks)
            
            # Move logits to CPU and convert to numpy array
            logits = logits.detach().cpu().numpy()
            
            # Get predicted label for each input sentence in the batch
            batch_predictions = np.argmax(logits, axis=1)
            predictions.extend(batch_predictions)

        # Combine predicted labels for all batches into a single list
        predicted_labels = []
        for batch in self.test_dataloader:
            # Append predicted labels for current batch to output list
            predicted_labels.extend(predictions[:len(batch[0])])
            
            # Remove predicted labels for current batch from predictions list
            predictions = predictions[len(batch[0]):]

        # Return predicted labels for all test sentences
        return predicted_labels

"""References"""

# https://arxiv.org/abs/2111.09543
# https://huggingface.co/yevheniimaslov/deberta-v3-base-cola/

"""# Runner Code"""

# import necessary libraries
import pandas as pd
import random
import numpy as np
from sklearn.metrics import confusion_matrix

# load training, validation, and testing data
train_df = pd.read_csv('/content/sample_data/train_data.csv')
val_df = pd.read_csv('/content/sample_data/val_data.csv')
test_df = pd.read_excel("/content/sample_data/test_data.xlsx")

# convert input column in test data to string
test_df['input'] = test_df['input'].astype(str)

# get sentences and labels from training and validation data
sentences_train = train_df['input'].tolist()
labels_train = train_df['labels'].tolist()

sentences_val = val_df['input'].tolist()
labels_val = val_df['labels'].tolist()

# get sentences from test data
sentences_test = test_df['input'].tolist()

# # Set the seed value all over the place to make this reproducible.
# seed_val = 42

# random.seed(seed_val)
# np.random.seed(seed_val)
# torch.manual_seed(seed_val)
# torch.cuda.manual_seed_all(seed_val)

# create DebertaDataset objects for the train, validation, and test datasets
train_dataset = DebertaDataset(sentences_train, labels_train, tokenizer_name='sileod/deberta-v3-base-tasksource-nli', batch_size=16)
val_dataset = DebertaDataset(sentences_val, labels_val, tokenizer_name='sileod/deberta-v3-base-tasksource-nli', batch_size=16)
test_dataset = DebertaDataset(sentences_test, tokenizer_name='sileod/deberta-v3-base-tasksource-nli', batch_size=16)

# create a DebertaTrainer object with specified parameters
deberta_model = DebertaTrainer(dataset_train=train_dataset, dataset_val=val_dataset, dataset_test=test_dataset,
                             num_classes=2,
                             learning_rate=2e-5,
                             eps=1e-8,
                             weight_decay=0.01,
                             betas=(0.9, 0.999),
                             num_epochs=2,
                             warmup_prop=0.1)

# train the Deberta model and save the best one
deberta_model.train()

# Final precision and F1-scores on validation set along with the confusion matrix
val_loss, val_f1, val_precision, confusion_matrix = deberta_model.evaluate()
print(f"Validation loss: {val_loss:.3f}, Validation F1 score: {val_f1:.3f}, Validation Precision: {val_precision:.3f}")
print(f"Confusion matrix:\n{confusion_matrix}")

# Test the model
test_preds = deberta_model.test()

"""# Saving the predictions of test data"""

print(len(test_preds))
# Write the test_sentence and corresponding predicted-label pairs to a CSV file
test_results = pd.DataFrame({"input": sentences_test, "labels": test_preds})
test_results.to_csv('anannyo_dey_submission.csv')