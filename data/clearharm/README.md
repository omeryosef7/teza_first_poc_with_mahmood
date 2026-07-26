---
dataset_info:
- config_name: default
  features:
  - name: clf_label
    dtype:
      class_label:
        names:
          '0': Benign
          '1': Harmful
  - name: instructions
    dtype: string
  - name: content
    sequence: string
  - name: answer_prompt
    dtype: string
  - name: proxy_clf_label
    dtype: int64
  - name: gen_target
    dtype: string
  - name: proxy_gen_target
    dtype: string
  splits:
  - name: train
    num_bytes: 33126
    num_examples: 179
  - name: validation
    num_bytes: 0
    num_examples: 0
  download_size: 13453
  dataset_size: 33126
- config_name: neg
  features:
  - name: clf_label
    dtype:
      class_label:
        names:
          '0': Benign
          '1': Harmful
  - name: instructions
    dtype: string
  - name: content
    sequence: string
  - name: answer_prompt
    dtype: string
  - name: proxy_clf_label
    dtype: int64
  - name: gen_target
    dtype: string
  - name: proxy_gen_target
    dtype: string
  splits:
  - name: train
    num_bytes: 0
    num_examples: 0
  - name: validation
    num_bytes: 0
    num_examples: 0
  download_size: 4268
  dataset_size: 0
- config_name: pos
  features:
  - name: clf_label
    dtype:
      class_label:
        names:
          '0': Benign
          '1': Harmful
  - name: instructions
    dtype: string
  - name: content
    sequence: string
  - name: answer_prompt
    dtype: string
  - name: proxy_clf_label
    dtype: int64
  - name: gen_target
    dtype: string
  - name: proxy_gen_target
    dtype: string
  splits:
  - name: train
    num_bytes: 33126
    num_examples: 179
  - name: validation
    num_bytes: 0
    num_examples: 0
  download_size: 13453
  dataset_size: 33126
- config_name: rep40
  features:
  - name: clf_label
    dtype:
      class_label:
        names:
          '0': Benign
          '1': Harmful
  - name: instructions
    dtype: string
  - name: content
    sequence: string
  - name: answer_prompt
    dtype: string
  - name: proxy_clf_label
    dtype: int64
  - name: gen_target
    dtype: string
  - name: proxy_gen_target
    dtype: string
  splits:
  - name: train
    num_bytes: 1325040
    num_examples: 7160
  - name: validation
    num_bytes: 0
    num_examples: 0
  download_size: 77335
  dataset_size: 1325040
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: validation
    path: data/validation-*
- config_name: neg
  data_files:
  - split: train
    path: neg/train-*
  - split: validation
    path: neg/validation-*
- config_name: pos
  data_files:
  - split: train
    path: pos/train-*
  - split: validation
    path: pos/validation-*
- config_name: rep40
  data_files:
  - split: train
    path: rep40/train-*
  - split: validation
    path: rep40/validation-*
---
