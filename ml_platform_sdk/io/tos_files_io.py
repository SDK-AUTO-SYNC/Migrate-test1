from typing import Optional, Dict
from collections.abc import Callable
import io
import torch
from PIL import Image

from ml_platform_sdk import initializer
from ml_platform_sdk.config import credential as auth_credential
from ml_platform_sdk.tos import tos


class TorchTOSDataset:

    def __init__(self,
                 manifest_info: Optional[Dict] = None,
                 decode: Optional[Callable] = None,
                 transform: Optional[Callable] = None,
                 target_transform: Optional[Callable] = None,
                 credential: Optional[auth_credential.Credential] = None):
        self.credential = credential or initializer.global_config.get_credential(
        )
        self.decode = decode
        self.transform = transform
        self.target_transform = target_transform
        buckets = manifest_info['buckets']
        keys = manifest_info['keys']
        annotations = manifest_info['annotations']
        assert buckets is not None and keys is not None and annotations is not None
        assert len(buckets) == len(keys) and len(buckets) == len(annotations)
        self.set_dataset_indices(buckets, keys, annotations)

    def set_dataset_indices(self, buckets, keys, annotations):
        self.buckets = buckets
        self.keys = keys
        self.annotations = annotations

    def __len__(self):
        return len(self.buckets)
    
    def _decode(self, raw_data):
        return Image.open(io.BytesIO(raw_data)).convert('RGB')

    def _target_transform(self, target):
        target = int(target['Result'][0]["Data"][0]["Label"])
        return target

    def __getitem__(self, index):
        torch.set_num_threads(1)
        # get each process a TOS client
        if not hasattr(self, "tos_client"):
            self.tos_client = tos.TOSClient(self.credential)
        bucket, key, annotation = self.buckets[index], self.keys[
            index], self.annotations[index]
        rsp = self.tos_client.get_object(bucket=bucket, key=key)
        data = rsp.read()
        rsp.close()
        if self.decode is not None:
            data = self.decode(data)
        else:
            data = self._decode(data)
        if self.transform is not None:
            data = self.transform(data)
        if self.target_transform is not None:
            annotation = self.target_transform(annotation)
        else:
            annotation = self._target_transform(annotation)
        return data, annotation
