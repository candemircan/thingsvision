import warnings
from dataclasses import dataclass, field
from typing import Any, Iterator
from tqdm import tqdm
import numpy as np
import os


@dataclass(init=True, repr=True)
class BaseExtractor:
    model_name: str
    pretrained: bool
    device: str
    model_path: str = None
    model_parameters: Any = field(default_factory=lambda: {})
    model: Any = None
    preprocess: Any = None

    def __post_init__(self) -> None:
        if not self.model:
            self.load_model()

    def show(self) -> str:
        warnings.warn(
            "\nThe .show() method is deprecated and will be removed in future versions. Use .show_model() instead.\n"
        )
        return self.show_model()

    def show_model(self) -> str:
        return self._show_model()

    def extract_features(
        self,
        batches: Iterator,
        module_name: str,
        flatten_acts: bool,
        output_dir: str = None,
        steps: int = 100,
    ) -> np.ndarray:
        """Extract hidden unit activations (at specified layer) for every image in the database.

        Parameters
        ----------
        batches : Iterator
            Mini-batches. Iterator with equally sized
            mini-batches, where each element is a
            subsample of the full (image) dataset.
        module_name : str
            Layer name. Name of neural network layer for
            which features should be extraced.
        flatten_acts : bool
            Whether activation tensor (e.g., activations
            from an early layer of the neural network model)
            should be transformed into a vector.
        output_dir : str, optional
            Path/to//output/directory. If defined, the extracted
            features will be iteratively (every steps batches)
            stored to disk as numpy files, freeing up memory space.
            Use this option if your dataset is too large or when extracting many features
            at once. The default is None, so that the features are kept
            in memory.
        steps : int, optional
            Extracted features will be saved to disk every steps batches.
            The default is 100. This is only used if output_dir is defined.

        Returns
        -------
        output : np.ndarray
            Returns the feature matrix (e.g., X \in \mathbb{R}^{n \times p} if head or flatten_acts = True).
        """
        valid_names = self.get_module_names()
        if not module_name in valid_names:
            raise ValueError(
                f"\n{module_name} is not a valid module name. Please choose a name from the following set of modules: {valid_names}\n"
            )

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        features = []
        image_ct, last_image_ct = 0, 0
        for i, batch in tqdm(
            enumerate(batches, start=1), desc="Batch", total=len(batches)
        ):
            features.append(self._extract_features(batch, module_name, flatten_acts))

            image_ct += len(batch)

            if output_dir and (
                i % steps == 0
                or i == len(batches)
            ):
                features_subset_file = os.path.join(
                    output_dir,
                    f"features_{last_image_ct}-{image_ct}.npy",
                )
                features_subset = np.vstack(features)
                np.save(features_subset_file, features_subset)
                features = []
                last_image_ct = image_ct

        print(
            f"...Features successfully extracted for all {image_ct} images in the database."
        )
        if output_dir:
            print(f"...Features saved to {output_dir}.")
            return None
        else:
            features = np.vstack(features)
            print(f"...Features shape: {features.shape}")

        return features

    def get_transformations(
        self, resize_dim: int = 256, crop_dim: int = 224, apply_center_crop: bool = True
    ) -> Any:
        """Load image transformations for a specific model. Image transformations depend on the backend."""
        if self.preprocess:
            return self.preprocess
        else:
            mean = [0.485, 0.456, 0.406]
            std = [0.229, 0.224, 0.225]
            composition = self.get_default_transformation(
                mean, std, resize_dim, crop_dim, apply_center_crop
            )
        return composition
