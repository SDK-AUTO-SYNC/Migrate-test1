import json
import math
import os

import numpy as np

from volcengine_ml_platform import constant
from volcengine_ml_platform.datasets.dataset import _Dataset
from volcengine_ml_platform.datasets.dataset import dataset_copy_file


class TextDataset(_Dataset):
    """
    TextDataset创建函数同 ``ImageDataset``

    """

    def download(self, local_path: str = "TextDataset", limit=-1):
        """把数据集从 TOS 下载到本地

        Args:
            local_path(str): 设置下载目录
            limit (int, optional): 设置最大下载数据条目
        """

        """download datasets from source

        Args:
            limit (int, optional): download size. Defaults to -1 (no limit).
        """
        if local_path:
            self.local_path = local_path

        self._create_manifest_dataset(
            manifest_keyword="TextURL",
        )

    def split(self, training_dir: str, testing_dir: str, ratio=0.8, random_state=0):
        """把数据集分割成两个数据集对象（测试集合训练集）

        Args:
            training_dir (str): 训练集输出目录
            testing_dir (str): 测试集输出目录
            ratio (float, optional): 训练集数据所占比例，默认为 0.8
            random_state (int, optional): 随机数种子

        Returns:
            返回两个数据集，第一个是训练集
        """

        """split datasets and return two datasets objects

        Args:
            training_dir (str): [output directory of training data]
            testing_dir (str): [output directory of testing data]
            ratio (float, optional): [training set split ratio].
                                    Defaults to 0.8.
            random_state (int, optional): [random seed]. Defaults to 0.

        Returns:
            two datasets, first one is the training set
        """
        if not self.created:
            raise Exception("datasets has not been created")
        line_count = self.data_count

        np.random.seed(random_state)
        test_index_set = set(
            np.random.choice(
                line_count,
                math.floor(line_count * (1 - ratio)),
                replace=False,
            ),
        )
        os.makedirs(testing_dir, exist_ok=True)
        os.makedirs(training_dir, exist_ok=True)

        train_dataset = TextDataset(local_path=training_dir)
        test_dataset = TextDataset(local_path=testing_dir)
        # set new datasets size
        test_dataset.data_count = math.floor(line_count * (1 - ratio))
        train_dataset.data_count = line_count - test_dataset.data_count

        # generate training and testing datasets's manifest file
        train_metadata_path = os.path.join(
            training_dir,
            constant.DATASET_LOCAL_METADATA_FILENAME,
        )
        test_metadata_path = os.path.join(
            testing_dir,
            constant.DATASET_LOCAL_METADATA_FILENAME,
        )
        with open(
            test_metadata_path,
            mode="w",
            encoding="utf-8",
        ) as testing_manifest_file:
            with open(
                train_metadata_path,
                mode="w",
                encoding="utf-8",
            ) as training_manifest_file:
                index = 0
                with open(self._manifest_path(), encoding="utf-8") as f:
                    for line in f:
                        manifest_line = json.loads(line)
                        if index in test_index_set:
                            dataset_copy_file(
                                manifest_line,
                                self.local_path,
                                testing_dir,
                            )
                            json.dump(manifest_line, testing_manifest_file)
                            testing_manifest_file.write("\n")
                        else:
                            dataset_copy_file(
                                manifest_line,
                                self.local_path,
                                training_dir,
                            )
                            json.dump(manifest_line, training_manifest_file)
                            training_manifest_file.write("\n")
                        index = index + 1

        train_dataset.created = True
        test_dataset.created = True
        return train_dataset, test_dataset
