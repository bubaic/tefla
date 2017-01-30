# -------------------------------------------------------------------#
# Written by Mrinal Haloi
# Contact: mrinal.haloi11@gmail.com
# Copyright 2016, Mrinal Haloi
# -------------------------------------------------------------------#
import tensorflow as tf

log_loss = tf.contrib.losses.log_loss


def log_loss_custom(predictions, labels, eps=1e-7, name='log'):
    """Define a log loss.

    Args:
        predictions: 2D tensor or array, [batch_size, num_classes] predictions of the network .
        labels: 2D or array tensor, [batch_size, num_classes]  ground truth labels or target labels.
        eps: a constant to set upper or lower limit for labels, smoothening factor
        name: Optional scope/name for op_scope.

    Returns:
        A tensor with the log loss.
    """
    with tf.name_scope(name):
        predictions = tf.to_float(predictions)
        labels = tf.to_float(labels)
        predictions = tf.clip_by_value(predictions, eps, 1 - eps)
        predictions.get_shape().assert_is_compatible_with(labels.get_shape())
        loss = -tf.reduce_mean(labels * tf.log(predictions))
        return loss


def kappa_loss(predictions, labels, y_pow=1, eps=1e-15, num_ratings=5, batch_size=32, name='kappa'):
    """Define a kappa loss, Its a continuous differentiable approximation of discrete kappa loss.

    Args:
        predictions: 2D tensor or array, [batch_size, num_classes] predictions of the network .
        labels: 2D tensor or array,[batch_size, num_classes]  ground truth labels or target labels.
        y_pow: int, to whcih the labels should be raised; useful if model diverge. e.g. y_pow=2
        num_ratings: numbers of rater to used, typically num_classes of the model
        batch_size: batch_size of the training or validation ops
        eps: a float, prevents divide by zero 
        name: Optional scope/name for op_scope.

    Returns:
        A tensor with the kappa loss.
    """
    with tf.name_scope(name):
        labels = tf.to_float(labels)
        repeat_op = tf.to_float(tf.tile(tf.reshape(
            tf.range(0, num_ratings), [num_ratings, 1]), [1, num_ratings]))
        repeat_op_sq = tf.square((repeat_op - tf.transpose(repeat_op)))
        weights = repeat_op_sq / tf.to_float((num_ratings - 1) ** 2)

        pred_ = predictions ** y_pow
        try:
            pred_norm = pred_ / \
                (eps + tf.reshape(tf.reduce_sum(pred_, 1), [-1, 1]))
        except:
            pred_norm = pred_ / \
                (eps + tf.reshape(tf.reduce_sum(pred_, 1), [batch_size, 1]))

        hist_rater_a = tf.reduce_sum(pred_norm, 0)
        hist_rater_b = tf.reduce_sum(labels, 0)

        conf_mat = tf.matmul(tf.transpose(pred_norm), labels)

        nom = tf.reduce_sum(weights * conf_mat)
        denom = tf.reduce_sum(weights * tf.matmul(tf.reshape(hist_rater_a, [
                              num_ratings, 1]), tf.reshape(hist_rater_b, [1, num_ratings])) / tf.to_float(batch_size))

        try:
            return -(1 - nom / denom)
        except:
            return -(1 - nom / (denom + eps))


def kappa_log_loss(predictions, labels, label_smoothing=0.0, y_pow=1, batch_size=32, log_scale=0.5, log_offset=0.50, name='kappa_log'):
    """Define a joint kappa and log loss, Kappa is a continuous differentiable approximation of discrete kappa loss.

    Args:
        predictions: 2D tensor or array, [batch_size, num_classes] predictions of the network .
        labels: 2D tensor or array,[batch_size, num_classes]  ground truth labels or target labels.
        label_smoothing: a float, used to smooth the labels for better generalization
                         if greater than 0 then smooth the labels.
        y_pow: int, to whcih the labels should be raised; useful if model diverge. e.g. y_pow=2
        num_ratings: numbers of rater to used, typically num_classes of the model
        batch_size: batch_size of the training or validation ops
        log_scale: a float, used to multiply the clipped log loss, e.g: 0.5
        log_offset:a float minimum log loss offset to substract from original log loss; e.g. 0.50
        name: Optional scope/name for op_scope.

    Returns:
        A tensor with the kappa log loss.
    """
    with tf.name_scope(name):
        num_classes = labels.get_shape()[-1].value
        labels = tf.cast(labels, predictions.dtype)
        if label_smoothing > 0:
            smooth_positives = 1.0 - label_smoothing
            smooth_negatives = label_smoothing / num_classes
            labels = labels * smooth_positives + smooth_negatives
        log_loss_res = log_loss(predictions, labels)
        kappa_loss_res = kappa_loss(
            predictions, labels, y_pow=y_pow, batch_size=batch_size)
        return kappa_loss_res + log_scale * (log_loss_res - log_offset)


def kappa_log_loss_clipped(predictions, labels, label_smoothing=0.0, y_pow=1, batch_size=32, log_scale=0.5, log_cutoff=0.80, name='kappa_log_clipped'):
    """Define a joint kappa and log loss; log loss is clipped by a defined min value; Kappa is a continuous differentiable approximation of discrete kappa loss.

    Args:
        predictions: 2D tensor or array, [batch_size, num_classes] predictions of the network .
        labels: 2D tensor or array,[batch_size, num_classes]  ground truth labels or target labels.
        label_smoothing: a float, used to smooth the labels for better generalization
                         if greater than 0 then smooth the labels.
        y_pow: int, to whcih the labels should be raised; useful if model diverge. e.g. y_pow=2
        num_ratings: numbers of rater to used, typically num_classes of the model
        batch_size: batch_size of the training or validation ops
        log_scale: a float, used to multiply the clipped log loss, e.g: 0.5
        log_cutoff:a float, minimum log loss value; e.g. 0.50
        name: Optional scope/name for op_scope.

    Returns:
        A tensor with the clipped kappa log loss.
    """
    with tf.name_scope(name):
        num_classes = labels.get_shape()[-1].value
        labels = tf.cast(labels, predictions.dtype)
        if label_smoothing > 0:
            smooth_positives = 1.0 - label_smoothing
            smooth_negatives = label_smoothing / num_classes
            labels = labels * smooth_positives + smooth_negatives
        log_loss_res = log_loss(predictions, labels)
        kappa_loss_res = kappa_loss(
            predictions, labels, y_pow=y_pow, batch_size=batch_size)
        return kappa_loss_res + log_scale * tf.clip_by_value(log_loss_res, log_cutoff, 10 ** 3)


def cross_entropy_loss(logits, labels, label_smoothing=0.0, weight=1.0, name='cross_entropy_loss'):
    """Define a cross entropy loss with label smoothing.
    Args:
        predictions: 2D tensor or array, [batch_size, num_classes] predictions of the network .
        labels: 2D tensor or array,[batch_size, num_classes]  ground truth labels or target labels.
        label_smoothing: a float, used to smooth the labels for better generalization
                        if greater than 0 then smooth the labels.
        weight: scale the loss by this factor.
        name: Optional scope/name for op_scope.
    Returns:
        A tensor with the cross entropy loss.
    """
    logits.get_shape().assert_is_compatible_with(labels.get_shape())
    with tf.name_scope(name):
        num_classes = labels.get_shape()[-1].value
        labels = tf.cast(labels, logits.dtype)
        if label_smoothing > 0:
            smooth_positives = 1.0 - label_smoothing
            smooth_negatives = label_smoothing / num_classes
            labels = labels * smooth_positives + smooth_negatives
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(
            logits, labels, name='xentropy')
        weight = tf.convert_to_tensor(
            weight, dtype=logits.dtype.base_dtype, name='loss_weight')
        loss = tf.mul(weight, tf.reduce_mean(cross_entropy), name='value')
        return loss


def l1_l2_regularizer(var, weight_l1=1.0, weight_l2=1.0, name='l1_l2_regularizer'):
    """Define a L2Loss, useful for regularize, i.e. weight decay.
    Args:
        var: tensor to regularize.
        weight_l1: an optional weight to modulate the l1 loss.
        weight_l2: an optional weight to modulate the l2 loss.
        name: Optional scope/name for op_scope.
    Returns:
        the l1+L2 loss op.
    """
    with tf.name_scope(name):
        weight_l1_t = tf.convert_to_tensor(
            weight_l1, dtype=var.dtype.base_dtype, name='weight_l1')
        weight_l2_t = tf.convert_to_tensor(
            weight_l2, dtype=var.dtype.base_dtype, name='weight_l2')
        reg_l1 = tf.mul(weight_l1_t, tf.reduce_sum(
            tf.abs(var)), name='value_l1')
        reg_l2 = tf.mul(weight_l2_t, tf.nn.l2_loss(var), name='value_l2')
        return tf.add(reg_l1, reg_l2, name='value')