

**GED Dataset Classification using DeBERTaV3 +CNN**

**Introduction**

The goal of this project is to classify sentences in the given dataset as either grammatically correct or incorrect. I used a DeBERTa-v3+CNN based

classifier model to perform this task.

**Exploratory Data Analysis (EDA)**

· We are given a training set, a validation set, and a test set with 19998, 10000, 10000 text samples resp. The former 2 contain sentences that have

been labeled as either grammatically correct (1) or incorrect (0), whereas the test set is unlabeled.

· I performed some basic EDA on the dataset, including checking for missing values and analyzing the distribution of labels and sentence lengths,

and also the most frequently encountered tokens.

· It was found that the datasets have no missing values and, in the training and validation sets, the labels are nearly equally distributed between 0s

and 1s.

· The sentence lengths are distributed as follows-

**Training**

11\.640114

7\.666548

0\.000000

10\.000000

319\.000000

**Validation**

11\.745900

7\.606045

0\.000000

10\.000000

133\.000000

**Testing**

11\.716600

11\.109034

1\.000000

10\.000000

841\.000000

**Mean**

**Standard deviation**

**Min**

**50%**

**Max**

· By plotting the scatter-plots of the same, one can observe that besides a few outliers we can safely take 128 as the maximum-length of input tokens,

thereby reducing the training time by half if 256 was used (later checked that it didn’t affect the model accuracy).

· I also found that the train and validation sets are both poorly annotated, as there are numerous examples even in the top 50 or so entries, where

sentences are classified as False Positives and False Negatives; and I also used Grammarly.com to confirm the same.

**Steps Followed**

The following steps were followed in the project:

1\. Data Preparation: The dataset was loaded from the .csv files from the given training, validation sets. The test data needed to be loaded from the

unconventional .xlsx file as the pd.read\_csv parser wasn’t working due to some errors in the file encoding.

2\. Preprocessing: The sentences were preprocessed by tokenizing them using a pre-trained AutoTokenizer 'sileod/deberta-v3-base-tasksource-nli' as

it’s recorded as the SOTA in 2023, for GED in the standard CoLA dataset achieving 87.15% accuracy. Special tokens [CLS] [SEP] etc. were

added, and they were further truncated or padded to a fixed length of 128, and converting them to input features for the model.

3\. Model Training and Validation: I used a DeBERTaV3 pre-trained model, and stacked a CNN layer on top of it to classify the sentences as either

grammatically correct or incorrect. The model was fine-tuned on the training set and validated on the validation set using the Cross-entropy loss

function and the Adam optimizer for 2 epochs, and also ran experiments with the recommended hyper-parameter settings of DeBERTaV3 to find

that a batch size of 16, learning rate of 2e-5, weight\_decay of 0.01, scheduled with a warmup\_prop of 0.1 gave stable results.

4\. Testing, Saving and Error Analysis: After fine-tuning the model I saved the ‘model.pt’ file of the model with the best accuracy. Later I reloaded

the same in the testing phase, ran it on the unlabeled test dataset to get the test predictions, which I saved as a ‘.csv’ file in form of ‘test\_sentence-

predicted\_label’ pairs. I also performed error analysis to identify the errors based on their nature, and identified patterns in the errors.

**Model Architecture**

I used a DeBERTaV3 pre-trained model, which is DeBERTa improved using ELECTRA-style (which itself performs better in GED tasks than BERT)

pre-training and I specifically used the ‘yevheniimaslov/deberta-v3-base-cola’ version which just gave a slightly better edge. I used the embeddings from

the last\_hidden\_state of the previous layer, applied dropout, and then passed it through a CNN block, with a softmax classifier to classify the sentences as

either grammatically correct or incorrect.

**Error Analysis**

· After fine-tuning the model, I analyzed the errors on the validation set to identify its types and the factors contributing to these errors.

· I found that the model had difficulty with informal (chat) types of vocabulary with emoticons

· Errors were often caused by ambiguity in sentence structure/meaning, or were actually correct predictions but mismatched with the wrong

annotations on the validation set.

**Epoch**

**Task**

**Precision**

0\.624

0\.645

0\.694

0\.638

**F1-Score**

0\.599

0\.616

0\.674

0\.605

**False Positives**

**False Negatives**

**Time (in mins)**

10:14

1

Training

Validation

Training

Validation

\-

\-

2695

\-

2851

2695

866

\-

770

866

01:27

10:09

01:27

01:28

2

**Final Validation**

0\.645

0\.616

**Conclusion**

In conclusion, I used a DeBERTaV3+CNN based GED classifier model to classify sentences in the given dataset as either grammatically correct or

incorrect. I performed basic EDA on the dataset, followed a standard data preprocessing pipeline, fine-tuned the model using cross-entropy loss and Adam

optimizer, and performed error analysis to identify the sources of errors made by the model. Based on the experiments of the error analysis, I refined the

model hyper-parameter settings and achieved improved performance. The references have already been hyperlinked above wherever used or mentioned.

