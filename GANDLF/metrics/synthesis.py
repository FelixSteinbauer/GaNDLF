import sys
import SimpleITK as sitk
import PIL.Image
import numpy as np
import torch
from torchmetrics import (
    StructuralSimilarityIndexMeasure,
    MeanSquaredError,
    MeanSquaredLogError,
    MeanAbsoluteError,
)
from GANDLF.utils import get_image_from_tensor


def structural_similarity_index(target, prediction, mask=None) -> torch.Tensor:
    """
    Computes the structural similarity index between the target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.
        mask (torch.Tensor, optional): The mask tensor. Defaults to None.

    Returns:
        torch.Tensor: The structural similarity index.
    """
    ssim = StructuralSimilarityIndexMeasure(return_full_image=True)
    _, ssim_idx_full_image = ssim(target, prediction)
    mask = torch.ones_like(ssim_idx_full_image) if mask is None else mask
    try:
        ssim_idx = ssim_idx_full_image[mask]
    except Exception as e:
        print(f"Error: {e}")
        if len(ssim_idx_full_image.shape) == 0:
            ssim_idx = torch.ones_like(mask) * ssim_idx_full_image
    return ssim_idx.mean()


def mean_squared_error(target, prediction) -> torch.Tensor:
    """
    Computes the mean squared error between the target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.
    """
    mse = MeanSquaredError()
    return mse(target, prediction)


def peak_signal_noise_ratio(target, prediction) -> torch.Tensor:
    """
    Computes the peak signal to noise ratio between the target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.
    """
    mse = mean_squared_error(target, prediction)
    return (
        10.0
        * torch.log10((torch.max(target) - torch.min(target)) ** 2)
        / (mse + sys.float_info.epsilon)
    )


def mean_squared_log_error(target, prediction) -> torch.Tensor:
    """
    Computes the mean squared log error between the target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.
    """
    mle = MeanSquaredLogError()
    return mle(target, prediction)


def mean_absolute_error(target, prediction) -> torch.Tensor:
    """
    Computes the mean absolute error between the target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.
    """
    mae = MeanAbsoluteError()
    return mae(target, prediction)


def _get_ncc_image(target, prediction) -> sitk.Image:
    """
    Computes normalized cross correlation image between target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.

    Returns:
        torch.Tensor: The normalized cross correlation image.
    """

    def __convert_to_grayscale(image: sitk.Image) -> sitk.Image:
        """
        Helper function to convert image to grayscale.

        Args:
            image (sitk.Image): The image to convert.

        Returns:
            sitk.Image: The converted image.
        """
        if "vector" in image.GetPixelIDTypeAsString().lower():
            temp_array = sitk.GetArrayFromImage(image)
            image_pil = PIL.Image.fromarray(
                np.moveaxis(temp_array[0, ...], 0, 2).astype(np.uint8)
            )
            image_pil_gray = image_pil.convert("L")
            return sitk.GetImageFromArray(image_pil_gray)
        else:
            return image

    target_image = __convert_to_grayscale(get_image_from_tensor(target))
    pred_image = __convert_to_grayscale(get_image_from_tensor(prediction))
    correlation_filter = sitk.FFTNormalizedCorrelationImageFilter()
    return correlation_filter.Execute(target_image, pred_image)


def ncc_mean(target, prediction) -> float:
    """
    Computes normalized cross correlation mean between target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.

    Returns:
        float: The normalized cross correlation mean.
    """
    stats_filter = sitk.StatisticsImageFilter()
    corr_image = _get_ncc_image(target, prediction)
    stats_filter.Execute(corr_image)
    return stats_filter.GetMean()


def ncc_std(target, prediction) -> float:
    """
    Computes normalized cross correlation standard deviation between target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.

    Returns:
        float: The normalized cross correlation standard deviation.
    """
    stats_filter = sitk.StatisticsImageFilter()
    corr_image = _get_ncc_image(target, prediction)
    stats_filter.Execute(corr_image)
    return stats_filter.GetSigma()


def ncc_max(target, prediction) -> float:
    """
    Computes normalized cross correlation maximum between target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.

    Returns:
        float: The normalized cross correlation maximum.
    """
    stats_filter = sitk.StatisticsImageFilter()
    corr_image = _get_ncc_image(target, prediction)
    stats_filter.Execute(corr_image)
    return stats_filter.GetMaximum()


def ncc_min(target, prediction) -> float:
    """
    Computes normalized cross correlation minimum between target and prediction.

    Args:
        target (torch.Tensor): The target tensor.
        prediction (torch.Tensor): The prediction tensor.

    Returns:
        float: The normalized cross correlation minimum.
    """
    stats_filter = sitk.StatisticsImageFilter()
    corr_image = _get_ncc_image(target, prediction)
    stats_filter.Execute(corr_image)
    return stats_filter.GetMinimum()
